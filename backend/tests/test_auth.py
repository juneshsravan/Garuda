import uuid
from datetime import datetime, timezone
import pytest
from fastapi import Depends
from sqlalchemy import select

from app.api.deps import require_admin
from app.main import app
from app.models.platform import AuditLog
from app.models.user import Session as UserSession, User
from app.core.security import hash_password, hash_token


# Temporary admin test endpoint for testing require_admin dependency
@app.get("/api/test-admin-only", tags=["Testing"])
def admin_only_endpoint(admin: User = Depends(require_admin)):
    return {"message": "Admin authorized", "admin_id": str(admin.id)}


def test_register_success(client, db):
    """Verifies user registration, Argon2 password hashing, session creation, and audit logging."""
    payload = {
        "email": "priya.sharma@example.com",
        "password": "Password123!",
        "full_name": "Priya Sharma",
    }
    headers = {"X-Forwarded-For": "203.0.113.1"}
    response = client.post("/api/auth/register", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "priya.sharma@example.com"
    assert data["user"]["full_name"] == "Priya Sharma"
    assert data["user"]["role"] == "user"
    assert data["user"]["is_active"] is True
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Refresh cookie must be set with httpOnly
    assert "refresh_token" in response.cookies
    cookie_val = response.cookies["refresh_token"]

    # Verify user saved in test DB with Argon2 hash
    user_db = db.execute(select(User).where(User.email == "priya.sharma@example.com")).scalar_one()
    assert user_db.password_hash.startswith("$argon2id$")
    assert user_db.password_hash != "Password123!"

    # Verify session saved with hashed refresh token
    session_db = db.execute(select(UserSession).where(UserSession.user_id == user_db.id)).scalar_one()
    assert session_db.refresh_token_hash == hash_token(cookie_val)
    assert session_db.revoked_at is None

    # Verify audit log recorded
    audit_db = db.execute(
        select(AuditLog).where(AuditLog.actor_user_id == user_db.id, AuditLog.action == "register")
    ).scalar_one()
    assert audit_db.entity_type == "user"


def test_register_duplicate_email(client):
    """Verifies registration fails with 409 Conflict when email is already registered."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Initial User",
    }
    headers = {"X-Forwarded-For": "203.0.113.2"}
    resp1 = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Second attempt with same email
    resp2 = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp2.status_code == 409
    data = resp2.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "email" in data["error"]["details"]


def test_register_validation_errors(client):
    """Verifies validation errors return field-level details in error.details."""
    headers = {"X-Forwarded-For": "203.0.113.3"}

    # Password too short (< 8 chars)
    resp_short_pw = client.post(
        "/api/auth/register",
        json={"email": "valid@example.com", "password": "short", "full_name": "Valid Name"},
        headers=headers,
    )
    assert resp_short_pw.status_code == 422
    err_pw = resp_short_pw.json()["error"]
    assert err_pw["code"] == "VALIDATION_ERROR"
    assert "password" in err_pw["details"]

    # Full name too short (< 2 chars)
    resp_short_name = client.post(
        "/api/auth/register",
        json={"email": "valid@example.com", "password": "ValidPassword123", "full_name": "A"},
        headers=headers,
    )
    assert resp_short_name.status_code == 422
    err_name = resp_short_name.json()["error"]
    assert err_name["code"] == "VALIDATION_ERROR"
    assert "full_name" in err_name["details"]

    # Invalid email format
    resp_invalid_email = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "ValidPassword123", "full_name": "Valid Name"},
        headers=headers,
    )
    assert resp_invalid_email.status_code == 422
    err_email = resp_invalid_email.json()["error"]
    assert err_email["code"] == "VALIDATION_ERROR"
    assert "email" in err_email["details"]


def test_login_identical_error_wrong_password_and_unknown_email(client, db):
    """Rule: Login fails with the EXACT same status code, error code, and message for unknown email and wrong password."""
    headers = {"X-Forwarded-For": "203.0.113.4"}

    # Register legitimate user
    client.post(
        "/api/auth/register",
        json={"email": "realuser@example.com", "password": "RealPassword123", "full_name": "Real User"},
        headers=headers,
    )

    # 1. Wrong password for existing user
    resp_wrong_pw = client.post(
        "/api/auth/login",
        json={"email": "realuser@example.com", "password": "WrongPassword999"},
        headers=headers,
    )
    assert resp_wrong_pw.status_code == 401
    err_wrong_pw = resp_wrong_pw.json()

    # 2. Non-existent email
    resp_unknown_email = client.post(
        "/api/auth/login",
        json={"email": "unknown_ghost@example.com", "password": "SomePassword123"},
        headers=headers,
    )
    assert resp_unknown_email.status_code == 401
    err_unknown_email = resp_unknown_email.json()

    # Verify IDENTICAL response structure, codes, and messages (prevents user enumeration)
    assert err_wrong_pw == err_unknown_email
    assert err_wrong_pw["error"]["code"] == "INVALID_CREDENTIALS"
    assert err_wrong_pw["error"]["message"] == "Invalid email or password."

    # Verify audit logs for both failed attempts
    failed_logs = db.execute(
        select(AuditLog).where(AuditLog.action == "failed_login")
    ).scalars().all()
    assert len(failed_logs) == 2


def test_login_success(client, db):
    """Verifies successful login, JWT token issuance, cookie creation, and audit logging."""
    headers = {"X-Forwarded-For": "203.0.113.5"}
    client.post(
        "/api/auth/register",
        json={"email": "login.test@example.com", "password": "MySecretPassword123", "full_name": "Login Tester"},
        headers=headers,
    )

    resp_login = client.post(
        "/api/auth/login",
        json={"email": "login.test@example.com", "password": "MySecretPassword123"},
        headers=headers,
    )
    assert resp_login.status_code == 200
    data = resp_login.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login.test@example.com"
    assert "refresh_token" in resp_login.cookies

    # Verify login audit log
    login_log = db.execute(
        select(AuditLog).where(AuditLog.action == "login")
    ).scalar_one()
    assert login_log.metadata_["email"] == "login.test@example.com"


def test_get_me_with_and_without_token(client):
    """Verifies /me endpoint returns user details with token and rejects requests without token."""
    headers = {"X-Forwarded-For": "203.0.113.6"}
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": "me.test@example.com", "password": "SecretPassword123", "full_name": "Me Tester"},
        headers=headers,
    )
    token = reg_resp.json()["access_token"]

    # 1. Without token -> 401 UNAUTHORIZED
    resp_no_token = client.get("/api/auth/me")
    assert resp_no_token.status_code == 401
    assert resp_no_token.json()["error"]["code"] == "UNAUTHORIZED"

    # 2. With valid token -> 200 OK
    resp_with_token = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_with_token.status_code == 200
    me_data = resp_with_token.json()
    assert me_data["user"]["email"] == "me.test@example.com"
    assert me_data["user"]["full_name"] == "Me Tester"


def test_get_me_tampered_token(client):
    """Verifies tampered token is rejected with 401 INVALID_TOKEN."""
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered_payload.signature"
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


def test_refresh_token_rotation(client, db):
    """Verifies refresh token rotation: old session revoked, new session created, new access token issued."""
    headers = {"X-Forwarded-For": "203.0.113.7"}
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": "rotation@example.com", "password": "Password123!", "full_name": "Rotation Tester"},
        headers=headers,
    )
    old_cookie = client.cookies["refresh_token"]
    old_hash = hash_token(old_cookie)

    # Call /refresh with the cookie
    refresh_resp = client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 200
    new_token_data = refresh_resp.json()
    assert "access_token" in new_token_data

    # A new cookie was issued
    new_cookie = client.cookies["refresh_token"]
    assert new_cookie != old_cookie
    new_hash = hash_token(new_cookie)

    # In DB: old session must be revoked
    old_session = db.execute(select(UserSession).where(UserSession.refresh_token_hash == old_hash)).scalar_one()
    assert old_session.revoked_at is not None

    # New session must be active
    new_session = db.execute(select(UserSession).where(UserSession.refresh_token_hash == new_hash)).scalar_one()
    assert new_session.revoked_at is None

    # Re-using old revoked cookie must FAIL (prevent replay attacks)
    client.cookies.set("refresh_token", old_cookie)
    replay_resp = client.post("/api/auth/refresh")
    assert replay_resp.status_code == 401
    assert replay_resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


def test_logout_revocation(client, db):
    """Verifies logout revokes the database session, clears cookie, and logs audit."""
    headers = {"X-Forwarded-For": "203.0.113.8"}
    client.post(
        "/api/auth/register",
        json={"email": "logout.test@example.com", "password": "Password123!", "full_name": "Logout Tester"},
        headers=headers,
    )
    cookie_val = client.cookies["refresh_token"]
    cookie_hash = hash_token(cookie_val)

    # Perform logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Successfully logged out."

    # Cookie cleared in response
    assert client.cookies.get("refresh_token") is None or client.cookies.get("refresh_token") == ""

    # Session in DB must be revoked
    session_db = db.execute(select(UserSession).where(UserSession.refresh_token_hash == cookie_hash)).scalar_one()
    assert session_db.revoked_at is not None

    # Subsequent refresh with revoked cookie fails
    client.cookies.set("refresh_token", cookie_val)
    revoked_refresh = client.post("/api/auth/refresh")
    assert revoked_refresh.status_code == 401

    # Verify audit log for logout
    logout_log = db.execute(select(AuditLog).where(AuditLog.action == "logout")).scalar_one()
    assert logout_log.entity_type == "session"


def test_rate_limiting_login_and_register(client):
    """Verifies in-memory rate limiting triggers 429 when exceeding 5 requests/min/IP."""
    ip_header = {"X-Forwarded-For": "198.51.100.99"}

    # Execute 5 requests
    for i in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"email": f"ratelimit_{i}@example.com", "password": "Password123!"},
            headers=ip_header,
        )
        assert resp.status_code == 401  # Normal credential failure within limit

    # 6th request from same IP must be rejected with 429 Too Many Requests
    resp_blocked = client.post(
        "/api/auth/login",
        json={"email": "ratelimit_blocked@example.com", "password": "Password123!"},
        headers=ip_header,
    )
    assert resp_blocked.status_code == 429
    err = resp_blocked.json()["error"]
    assert err["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Too many requests" in err["message"]


def test_require_admin_dependency(client, db):
    """Verifies require_admin dependency allows admins and forbids standard users."""
    headers = {"X-Forwarded-For": "203.0.113.10"}

    # 1. Register regular user (role="user")
    reg_user = client.post(
        "/api/auth/register",
        json={"email": "regular.user@example.com", "password": "Password123!", "full_name": "Regular User"},
        headers=headers,
    )
    user_token = reg_user.json()["access_token"]

    resp_forbidden = client.get("/api/test-admin-only", headers={"Authorization": f"Bearer {user_token}"})
    assert resp_forbidden.status_code == 403
    assert resp_forbidden.json()["error"]["code"] == "FORBIDDEN"

    # 2. Create admin user (role="admin")
    admin_user = User(
        email="admin.boss@example.com",
        password_hash=hash_password("AdminPassword123!"),
        full_name="Admin Boss",
        role="admin",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    login_admin = client.post(
        "/api/auth/login",
        json={"email": "admin.boss@example.com", "password": "AdminPassword123!"},
        headers=headers,
    )
    admin_token = login_admin.json()["access_token"]

    resp_admin = client.get("/api/test-admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    assert resp_admin.json()["message"] == "Admin authorized"
