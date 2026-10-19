from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from sqlalchemy import select

from app.api.routes.auth import reset_resend_cooldowns
from app.core.config import settings
from app.models.user import EmailVerificationCode, User


def test_register_then_login_403_until_verified(client, db, mock_email_sender):
    """Rule: Register -> login 403 EMAIL_NOT_VERIFIED until verified."""
    email = "verify.first@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.201"}

    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Verify First"},
        headers=headers,
    )
    assert reg_resp.status_code == 201
    assert mock_email_sender.called
    sent_args = mock_email_sender.call_args[0]
    assert sent_args[0] == email
    dispatched_code = sent_args[1]
    assert len(dispatched_code) == 6
    assert dispatched_code.isdigit()

    # DB check: is_email_verified is False
    user_db = db.execute(select(User).where(User.email == email)).scalar_one()
    assert user_db.is_email_verified is False
    assert user_db.email_verified_at is None

    # 2. Login returns 403 EMAIL_NOT_VERIFIED
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers=headers,
    )
    assert login_resp.status_code == 403
    err = login_resp.json()["error"]
    assert err["code"] == "EMAIL_NOT_VERIFIED"
    assert "Email verification is required" in err["message"]


def test_correct_code_verifies_and_login_works(client, db, mock_email_sender):
    """Rule: Correct 6-digit code -> email verified -> login works with 200."""
    email = "success.verify@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.202"}

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Success Verify"},
        headers=headers,
    )
    code = mock_email_sender.call_args[0][1]

    # Verify email
    v_resp = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code},
        headers=headers,
    )
    assert v_resp.status_code == 200
    assert "Email verified successfully" in v_resp.json()["message"]

    # Direct DB check
    user_db = db.execute(select(User).where(User.email == email)).scalar_one()
    assert user_db.is_email_verified is True
    assert user_db.email_verified_at is not None

    # Code in DB is marked as used
    code_db = db.execute(
        select(EmailVerificationCode).where(EmailVerificationCode.user_id == user_db.id)
    ).scalar_one()
    assert code_db.used_at is not None

    # Login now succeeds with 200
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers=headers,
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
    assert login_resp.json()["user"]["is_email_verified"] is True


def test_wrong_code_five_attempts_blocked(client, db, mock_email_sender):
    """Rule: Wrong code 5 times -> blocked (MAX_ATTEMPTS_EXCEEDED). Correct code afterwards fails."""
    email = "wrong.attempts@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.203"}

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Wrong Attempts"},
        headers=headers,
    )
    correct_code = mock_email_sender.call_args[0][1]
    wrong_code = "999999" if correct_code != "999999" else "888888"

    # Attempts 1 to 4: returns 400 with remaining count
    for attempt in range(1, 5):
        resp = client.post(
            "/api/auth/verify-email",
            json={"email": email, "code": wrong_code},
            headers=headers,
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == "INVALID_CODE"
        remaining = 5 - attempt
        assert f"{remaining} attempt" in err["message"]

    # 5th wrong attempt: triggers MAX_ATTEMPTS_EXCEEDED
    resp_5th = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": wrong_code},
        headers=headers,
    )
    assert resp_5th.status_code == 400
    assert resp_5th.json()["error"]["code"] == "MAX_ATTEMPTS_EXCEEDED"

    # Even submitting the CORRECT code on 6th attempt is blocked
    resp_after_lock = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": correct_code},
        headers=headers,
    )
    assert resp_after_lock.status_code == 400
    assert resp_after_lock.json()["error"]["code"] == "MAX_ATTEMPTS_EXCEEDED"


def test_expired_code_fails(client, db, mock_email_sender):
    """Rule: A code past 10 minutes expiry fails with CODE_EXPIRED."""
    email = "expired.code@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.204"}

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Expired Code"},
        headers=headers,
    )
    code = mock_email_sender.call_args[0][1]

    # Manually expire the code in the database
    user_db = db.execute(select(User).where(User.email == email)).scalar_one()
    code_db = db.execute(
        select(EmailVerificationCode).where(EmailVerificationCode.user_id == user_db.id)
    ).scalar_one()
    code_db.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    # Attempt to verify with the expired code
    resp = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code},
        headers=headers,
    )
    assert resp.status_code == 400
    err = resp.json()["error"]
    assert err["code"] == "CODE_EXPIRED"
    assert "Verification code has expired" in err["message"]


def test_two_resends_give_different_codes_and_old_ones_fail(client, db, mock_email_sender):
    """Rule: Two resends generate different codes, and previous codes are invalidated immediately."""
    email = "resend.cycle@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.205"}

    # 1. Register -> Code 1
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Resend Cycle"},
        headers=headers,
    )
    code1 = mock_email_sender.call_args[0][1]

    # Reset cooldown so we can test code invalidation on resend
    reset_resend_cooldowns()

    # 2. Resend 1 -> Code 2
    resend1_resp = client.post(
        "/api/auth/resend-code",
        json={"email": email},
        headers=headers,
    )
    assert resend1_resp.status_code == 200
    code2 = mock_email_sender.call_args[0][1]
    assert code2 != code1

    # Old Code 1 must fail immediately
    fail_old_resp = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code1},
        headers=headers,
    )
    assert fail_old_resp.status_code == 400
    assert fail_old_resp.json()["error"]["code"] == "INVALID_CODE"

    # Reset cooldown for second resend
    reset_resend_cooldowns()

    # 3. Resend 2 -> Code 3
    resend2_resp = client.post(
        "/api/auth/resend-code",
        json={"email": email},
        headers=headers,
    )
    assert resend2_resp.status_code == 200
    code3 = mock_email_sender.call_args[0][1]
    assert code3 != code2
    assert code3 != code1

    # Old Code 2 must fail immediately
    fail_code2_resp = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code2},
        headers=headers,
    )
    assert fail_code2_resp.status_code == 400

    # Newest Code 3 succeeds!
    success_resp = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code3},
        headers=headers,
    )
    assert success_resp.status_code == 200


def test_used_code_cannot_be_reused(client, db, mock_email_sender):
    """Rule: A used verification code cannot be reused."""
    email = "used.code@example.com"
    password = "StrongPassword123!"
    headers = {"X-Forwarded-For": "203.0.113.206"}

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Used Code Tester"},
        headers=headers,
    )
    code = mock_email_sender.call_args[0][1]

    # First verification -> 200
    resp1 = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code},
        headers=headers,
    )
    assert resp1.status_code == 200

    # Second verification attempt with same code
    resp2 = client.post(
        "/api/auth/verify-email",
        json={"email": email, "code": code},
        headers=headers,
    )
    # Already verified message or invalid code error
    assert resp2.status_code in (200, 400)
    if resp2.status_code == 200:
        assert "already verified" in resp2.json()["message"].lower()


def test_resend_rate_limit(client, db, mock_email_sender):
    """Rule: Resend code is rate limited to once per 60 seconds. Does not reveal if email exists."""
    email = "ratelimit.resend@example.com"
    headers = {"X-Forwarded-For": "203.0.113.207"}

    # User exists
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Rate Limit Tester"},
        headers=headers,
    )
    reset_resend_cooldowns()

    # 1st resend succeeds
    res1 = client.post("/api/auth/resend-code", json={"email": email}, headers=headers)
    assert res1.status_code == 200

    # 2nd resend within 60 seconds returns 429 RATE_LIMIT_EXCEEDED
    res2 = client.post("/api/auth/resend-code", json={"email": email}, headers=headers)
    assert res2.status_code == 429
    err = res2.json()["error"]
    assert err["code"] == "RATE_LIMIT_EXCEEDED"
    assert "60 seconds" in err["message"]

    # Non-existent email also gets identical rate limiting without revealing existence
    ghost_email = "ghost.nonexistent@example.com"
    reset_resend_cooldowns()

    ghost_res1 = client.post("/api/auth/resend-code", json={"email": ghost_email}, headers=headers)
    assert ghost_res1.status_code == 200
    assert "If the email is registered" in ghost_res1.json()["message"]

    ghost_res2 = client.post("/api/auth/resend-code", json={"email": ghost_email}, headers=headers)
    assert ghost_res2.status_code == 429
    assert ghost_res2.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
