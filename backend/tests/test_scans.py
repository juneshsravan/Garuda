import uuid
import pytest
from sqlalchemy import select

from app.models.scan import (
    AnalysisResult,
    Message,
    Scan,
    ThreatIndicator,
    URL,
)
from app.models.user import User

_test_ip_counter = 10


def register_and_get_token(client, email: str = "scanner@example.com") -> tuple[str, dict]:
    """Helper to register a user and return the Bearer access token and user info with distinct IP."""
    global _test_ip_counter
    _test_ip_counter += 1
    headers = {"X-Forwarded-For": f"203.0.113.{_test_ip_counter}"}

    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Scanner Tester",
    }
    resp = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]


def test_register_email_verified_at_stays_null(client, db):
    """Rule: When registering with EMAIL_VERIFICATION_REQUIRED=false, email_verified_at must stay null in DB and response."""
    email = "unverified.registration@example.com"
    token, user_data = register_and_get_token(client, email=email)

    # 1. API response check
    assert user_data["email_verified_at"] is None
    assert user_data["is_active"] is True

    # 2. Database direct check
    db_user = db.execute(select(User).where(User.email == email)).scalar_one()
    assert db_user.email_verified_at is None
    assert db_user.is_active is True


def test_analyze_message_qr_reward_high_and_saved_in_all_tables(client, db):
    """
    Rule: The ₹500 QR reward message is High risk and saved across scans, messages,
    analysis_results (including legitimacy_signals), and threat_indicators in one transaction.
    """
    token, user_info = register_and_get_token(client, email="qr.tester@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    qr_text = "Congratulations! You won ₹500. Scan this QR immediately to claim your reward."
    payload = {"text": qr_text, "save": True}

    response = client.post("/api/analyze/message", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    scan_id_str = data["scan_id"]
    assert scan_id_str is not None
    scan_uuid = uuid.UUID(scan_id_str)

    # Risk level must be High (score >= 65) per ARCHITECTURE 8.5
    assert data["risk"]["level"] == "high"
    assert data["risk"]["score"] >= 65
    assert data["scan_type"] == "message"
    assert data["category"]["code"] is not None
    assert len(data["indicators"]) > 0
    assert "legitimacy_signals" in data
    assert "recommendations" in data
    assert "verify_steps" in data

    # Verify atomic persistence in ALL tables
    # 1. scans table
    scan_row = db.execute(select(Scan).where(Scan.id == scan_uuid)).scalar_one()
    assert str(scan_row.user_id) == user_info["id"]
    assert scan_row.scan_type == "message"
    assert scan_row.status == "done"
    assert scan_row.persisted_content is True
    assert scan_row.input_sha256 is not None

    # 2. messages table
    msg_row = db.execute(select(Message).where(Message.scan_id == scan_uuid)).scalar_one()
    assert msg_row.content == qr_text

    # 3. analysis_results table
    analysis_row = db.execute(select(AnalysisResult).where(AnalysisResult.scan_id == scan_uuid)).scalar_one()
    assert analysis_row.risk_level == "high"
    assert analysis_row.risk_score == data["risk"]["score"]
    assert analysis_row.category == data["category"]["code"]
    assert isinstance(analysis_row.legitimacy_signals, list)

    # 4. threat_indicators table
    ti_rows = db.execute(
        select(ThreatIndicator).where(ThreatIndicator.analysis_id == analysis_row.id)
    ).scalars().all()
    assert len(ti_rows) == len(data["indicators"])
    ti_codes = {ti.code for ti in ti_rows}
    assert len(ti_codes) > 0


def test_analyze_message_urls_saved_with_source_message(client, db):
    """
    Rule: URLs detected in the message are saved into the urls table with source='message' in the same transaction.
    """
    token, _ = register_and_get_token(client, email="url.msg@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    phish_msg = (
        "Income Tax Dept: You are eligible for a refund of ₹15,490. "
        "Submit your bank details at http://incometax-refund.co.in-claim.top immediately."
    )
    payload = {"text": phish_msg, "save": True}

    resp = client.post("/api/analyze/message", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    scan_id = uuid.UUID(data["scan_id"])

    # Verify URLs table
    url_rows = db.execute(select(URL).where(URL.scan_id == scan_id)).scalars().all()
    assert len(url_rows) >= 1
    u = url_rows[0]
    assert u.source == "message"
    assert "incometax-refund.co.in-claim.top" in u.raw_url


def test_analyze_message_hdfc_otp_likely_safe(client):
    """Rule: Standard HDFC OTP message is Likely Safe with legitimacy signals."""
    token, _ = register_and_get_token(client, email="hdfc.tester@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    hdfc_text = (
        "Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. "
        "Valid for 10 mins. Do NOT share OTP or password with anyone. "
        "Bank NEVER calls for OTP - HDFC Bank"
    )
    payload = {"text": hdfc_text, "save": True}

    response = client.post("/api/analyze/message", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["risk"]["level"] == "likely_safe"
    assert data["risk"]["score"] <= 24
    assert len(data["legitimacy_signals"]) > 0


def test_analyze_message_save_false_stores_nothing(client, db):
    """Rule: When save=false, analysis is returned but NOTHING is stored in the database."""
    token, user_info = register_and_get_token(client, email="nosave@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    text = "Congratulations! You won ₹500. Scan this QR immediately to claim your reward."
    payload = {"text": text, "save": False}

    response = client.post("/api/analyze/message", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scan_id"] is None

    # Check database: 0 records in scans, messages, analysis_results, threat_indicators, urls
    scans_count = db.execute(select(Scan)).scalars().all()
    messages_count = db.execute(select(Message)).scalars().all()
    analysis_count = db.execute(select(AnalysisResult)).scalars().all()
    indicators_count = db.execute(select(ThreatIndicator)).scalars().all()
    urls_count = db.execute(select(URL)).scalars().all()

    assert len(scans_count) == 0
    assert len(messages_count) == 0
    assert len(analysis_count) == 0
    assert len(indicators_count) == 0
    assert len(urls_count) == 0


def test_idor_user_a_cannot_read_or_delete_user_b_scan(client):
    """
    Rule: GET /api/scans/{id} and DELETE /api/scans/{id} return 404 if the scan
    belongs to another user (prevents IDOR and existence probing).
    """
    token_a, _ = register_and_get_token(client, email="user_a@example.com")
    token_b, _ = register_and_get_token(client, email="user_b@example.com")

    # User A creates a scan
    resp_create = client.post(
        "/api/analyze/message",
        json={"text": "User A secret message to scan.", "save": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_create.status_code == 200
    scan_id_a = resp_create.json()["scan_id"]

    # 1. User B attempts GET /api/scans/{scan_id_a} -> MUST return 404
    resp_b_get = client.get(
        f"/api/scans/{scan_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b_get.status_code == 404
    assert resp_b_get.json()["error"]["code"] == "NOT_FOUND"

    # 2. User B attempts DELETE /api/scans/{scan_id_a} -> MUST return 404
    resp_b_del = client.delete(
        f"/api/scans/{scan_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b_del.status_code == 404
    assert resp_b_del.json()["error"]["code"] == "NOT_FOUND"

    # 3. User A CAN read their own scan -> 200 OK
    resp_a_get = client.get(
        f"/api/scans/{scan_id_a}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a_get.status_code == 200
    assert resp_a_get.json()["scan_id"] == scan_id_a

    # 4. User B listing scans only sees their own (empty)
    resp_b_list = client.get(
        "/api/scans",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b_list.status_code == 200
    assert len(resp_b_list.json()["items"]) == 0


def test_delete_scan_removes_scan_and_all_linked_rows(client, db):
    """Rule: DELETE /api/scans/{id} deletes the scan and all linked records via cascade."""
    token, _ = register_and_get_token(client, email="delete.tester@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    phish_msg = "You won ₹500 at http://claim500.in immediately."
    resp_create = client.post(
        "/api/analyze/message",
        json={"text": phish_msg, "save": True},
        headers=headers,
    )
    scan_id_str = resp_create.json()["scan_id"]
    scan_id = uuid.UUID(scan_id_str)

    # Ensure linked records exist before delete
    assert db.execute(select(Scan).where(Scan.id == scan_id)).scalar_one_or_none() is not None
    assert db.execute(select(Message).where(Message.scan_id == scan_id)).scalar_one_or_none() is not None
    analysis = db.execute(select(AnalysisResult).where(AnalysisResult.scan_id == scan_id)).scalar_one_or_none()
    assert analysis is not None
    assert len(db.execute(select(ThreatIndicator).where(ThreatIndicator.analysis_id == analysis.id)).scalars().all()) > 0
    assert len(db.execute(select(URL).where(URL.scan_id == scan_id)).scalars().all()) > 0

    # Execute DELETE /api/scans/{id}
    del_resp = client.delete(f"/api/scans/{scan_id_str}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Scan deleted successfully."

    # Verify ALL tables have 0 rows linked to this scan
    assert db.execute(select(Scan).where(Scan.id == scan_id)).scalar_one_or_none() is None
    assert db.execute(select(Message).where(Message.scan_id == scan_id)).scalar_one_or_none() is None
    assert db.execute(select(AnalysisResult).where(AnalysisResult.scan_id == scan_id)).scalar_one_or_none() is None
    assert len(db.execute(select(ThreatIndicator).where(ThreatIndicator.analysis_id == analysis.id)).scalars().all()) == 0
    assert len(db.execute(select(URL).where(URL.scan_id == scan_id)).scalars().all()) == 0


def test_unauthenticated_requests_rejected(client):
    """Rule: Unauthenticated requests to analyze and scans endpoints return 401 UNAUTHORIZED."""
    fake_id = str(uuid.uuid4())

    assert client.post("/api/analyze/message", json={"text": "Hello", "save": True}).status_code == 401
    assert client.get("/api/scans").status_code == 401
    assert client.get(f"/api/scans/{fake_id}").status_code == 401
    assert client.delete(f"/api/scans/{fake_id}").status_code == 401


def test_empty_and_too_long_text_rejected(client):
    """Rule: Message analyze rejects empty string, whitespace only, and text > 5000 chars with 422."""
    token, _ = register_and_get_token(client, email="validation.text@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Empty string
    resp_empty = client.post("/api/analyze/message", json={"text": "", "save": True}, headers=headers)
    assert resp_empty.status_code == 422
    assert resp_empty.json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Whitespace only
    resp_whitespace = client.post("/api/analyze/message", json={"text": "    \n   ", "save": True}, headers=headers)
    assert resp_whitespace.status_code == 422
    assert resp_whitespace.json()["error"]["code"] == "VALIDATION_ERROR"

    # 3. Too long (> 5000 chars)
    resp_long = client.post("/api/analyze/message", json={"text": "A" * 5001, "save": True}, headers=headers)
    assert resp_long.status_code == 422
    assert resp_long.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_scans_pagination_and_filters(client):
    """Rule: GET /api/scans provides newest-first ordering, cursor pagination, and filtering by scan_type and risk_level."""
    token, _ = register_and_get_token(client, email="pagination.tester@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Scan 1: High risk
    client.post(
        "/api/analyze/message",
        json={"text": "Congratulations! You won ₹500. Scan this QR immediately.", "save": True},
        headers=headers,
    )
    # Create Scan 2: Likely Safe
    client.post(
        "/api/analyze/message",
        json={"text": "Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. Valid for 10 mins. Bank NEVER calls for OTP - HDFC Bank", "save": True},
        headers=headers,
    )
    # Create Scan 3: High risk
    client.post(
        "/api/analyze/message",
        json={"text": "Income Tax Dept: You are eligible for a refund of ₹15,490. Submit your bank details at http://incometax-refund.co.in-claim.top", "save": True},
        headers=headers,
    )

    # 1. Test pagination limit=2
    page1 = client.get("/api/scans?limit=2", headers=headers)
    assert page1.status_code == 200
    p1_data = page1.json()
    assert len(p1_data["items"]) == 2
    assert p1_data["has_more"] is True
    assert p1_data["next_cursor"] is not None

    # Fetch page 2 using cursor
    cursor = p1_data["next_cursor"]
    page2 = client.get(f"/api/scans?limit=2&cursor={cursor}", headers=headers)
    assert page2.status_code == 200
    p2_data = page2.json()
    assert len(p2_data["items"]) == 1
    assert p2_data["has_more"] is False
    assert p2_data["next_cursor"] is None

    # 2. Test filter by risk_level=high
    high_resp = client.get("/api/scans?risk_level=high", headers=headers)
    assert high_resp.status_code == 200
    high_items = high_resp.json()["items"]
    assert len(high_items) == 2
    assert all(item["risk"]["level"] == "high" for item in high_items)

    # 3. Test filter by risk_level=likely_safe
    safe_resp = client.get("/api/scans?risk_level=likely_safe", headers=headers)
    assert safe_resp.status_code == 200
    safe_items = safe_resp.json()["items"]
    assert len(safe_items) == 1
    assert safe_items[0]["risk"]["level"] == "likely_safe"

    # 4. Test filter by scan_type=message
    msg_resp = client.get("/api/scans?scan_type=message", headers=headers)
    assert msg_resp.status_code == 200
    assert len(msg_resp.json()["items"]) == 3
