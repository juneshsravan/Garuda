import uuid
import pytest
from datetime import datetime, timezone

_test_ip_seq = 200


def register_user(client, email: str, name: str = "Report Tester") -> str:
    """Helper to register a user and return the Bearer access token."""
    global _test_ip_seq
    _test_ip_seq += 1
    headers = {"X-Forwarded-For": f"203.0.113.{_test_ip_seq}"}
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": name,
    }
    resp = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["access_token"]


def test_no_login_401(client):
    """Rule: Unauthenticated requests to reports endpoints return 401."""
    # 1. POST
    resp = client.post("/api/reports", json={"scam_type": "sms", "content": "Scam message"})
    assert resp.status_code == 401

    # 2. GET list
    resp = client.get("/api/reports")
    assert resp.status_code == 401

    # 3. GET detail
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/reports/{fake_id}")
    assert resp.status_code == 401


def test_create_report_success_and_validation(client):
    """
    Rule: Valid report creation returns 201 with generated reference code GAR-{year}-{seq:06d},
    status 'submitted', and validates all inputs and size limits.
    """
    token = register_user(client, "reporter1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Successful creation with all fields
    payload = {
        "scam_type": "whatsapp",
        "content": "Electricity power disconnection threat message with officer number",
        "scammer_phone": "+91 9876543210",
        "scammer_upi": "electricity.officer@ybl",
        "scammer_url": "https://fake-bijli-bill.xyz/pay",
        "amount_lost": 2500.50,
        "incident_date": "2026-10-18T10:30:00Z",
    }
    resp = client.post("/api/reports", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["scam_type"] == "whatsapp"
    assert data["content"] == payload["content"]
    assert data["scammer_phone"] == payload["scammer_phone"]
    assert data["scammer_upi"] == payload["scammer_upi"]
    assert data["scammer_url"] == payload["scammer_url"]
    assert data["amount_lost"] == 2500.50
    assert data["status"] == "submitted"
    assert "reference_code" in data
    assert data["reference_code"].startswith(f"GAR-{datetime.now(timezone.utc).year}-")

    # 2. Input validation: invalid scam_type -> 422
    bad_type = {**payload, "scam_type": "invalid_vector"}
    resp = client.post("/api/reports", json=bad_type, headers=headers)
    assert resp.status_code == 422

    # 3. Input validation: empty content -> 422
    empty_content = {**payload, "content": "   "}
    resp = client.post("/api/reports", json=empty_content, headers=headers)
    assert resp.status_code == 422

    # 4. Input validation: content over 5000 chars -> 422
    oversized = {**payload, "content": "A" * 5001}
    resp = client.post("/api/reports", json=oversized, headers=headers)
    assert resp.status_code == 422


def test_list_only_own_reports(client):
    """
    Rule: GET /api/reports returns ONLY the authenticated user's reports, newest first.
    Never exposes another user's reports.
    """
    token_a = register_user(client, "user_a@example.com")
    token_b = register_user(client, "user_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates 2 reports
    resp_a1 = client.post(
        "/api/reports",
        json={"scam_type": "sms", "content": "User A first report"},
        headers=headers_a,
    )
    assert resp_a1.status_code == 201
    id_a1 = resp_a1.json()["id"]

    resp_a2 = client.post(
        "/api/reports",
        json={"scam_type": "call", "content": "User A second report"},
        headers=headers_a,
    )
    assert resp_a2.status_code == 201
    id_a2 = resp_a2.json()["id"]

    # User B creates 1 report
    resp_b1 = client.post(
        "/api/reports",
        json={"scam_type": "link", "content": "User B report", "scammer_url": "https://phish.top"},
        headers=headers_b,
    )
    assert resp_b1.status_code == 201
    id_b1 = resp_b1.json()["id"]

    # User A lists reports -> exactly 2 reports, matching A's IDs
    list_a = client.get("/api/reports", headers=headers_a)
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert len(items_a) == 2
    ids_a = {item["id"] for item in items_a}
    assert ids_a == {id_a1, id_a2}
    assert id_b1 not in ids_a

    # User B lists reports -> exactly 1 report, matching B's ID
    list_b = client.get("/api/reports", headers=headers_b)
    assert list_b.status_code == 200
    items_b = list_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == id_b1


def test_other_user_gets_404_on_report_detail(client):
    """
    Rule: GET /api/reports/{id} returns 404 if the report belongs to another user
    (never 403 or disclosure of existence).
    """
    token_a = register_user(client, "owner_a@example.com")
    token_b = register_user(client, "snooper_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a report
    resp = client.post(
        "/api/reports",
        json={"scam_type": "qr_upi", "content": "User A private report"},
        headers=headers_a,
    )
    assert resp.status_code == 201
    report_id = resp.json()["id"]

    # User A can view their own report -> 200
    view_a = client.get(f"/api/reports/{report_id}", headers=headers_a)
    assert view_a.status_code == 200
    assert view_a.json()["id"] == report_id

    # User B tries to view User A's report -> 404 Not Found
    view_b = client.get(f"/api/reports/{report_id}", headers=headers_b)
    assert view_b.status_code == 404
    err = view_b.json()["error"]
    assert err["code"] == "REPORT_NOT_FOUND"


def test_community_warning_after_2_different_users(client):
    """
    Rule: When a URL, UPI, or phone has been reported by 2+ DIFFERENT users,
    analysis adds indicator COMMUNITY_REPORTED (medium, weight 0.4, 'Reported by N GARUDA users').
    Never triggers with 0 or 1 user, or with the same user reporting twice.
    Never reveals who reported.
    """
    token_u1 = register_user(client, "community_user1@example.com")
    token_u2 = register_user(client, "community_user2@example.com")
    token_scanner = register_user(client, "community_scanner@example.com")

    h_u1 = {"Authorization": f"Bearer {token_u1}"}
    h_u2 = {"Authorization": f"Bearer {token_u2}"}
    h_scanner = {"Authorization": f"Bearer {token_scanner}"}

    target_url = "http://community-scam-target.xyz/login"
    target_phone = "9876500001"
    target_upi = "scammer.collect@oksbi"

    # 1. Initial scan: 0 reports -> No COMMUNITY_REPORTED indicator
    url_scan1 = client.post("/api/analyze/url", json={"url": target_url, "save": False}, headers=h_scanner)
    assert url_scan1.status_code == 200
    assert not any(i["code"] == "COMMUNITY_REPORTED" for i in url_scan1.json()["indicators"])

    # 2. User 1 submits a report containing target_url
    rep1 = client.post(
        "/api/reports",
        json={"scam_type": "link", "content": "Phishing link report", "scammer_url": target_url},
        headers=h_u1,
    )
    assert rep1.status_code == 201

    # Still only 1 user reported -> No COMMUNITY_REPORTED indicator
    url_scan2 = client.post("/api/analyze/url", json={"url": target_url, "save": False}, headers=h_scanner)
    assert url_scan2.status_code == 200
    assert not any(i["code"] == "COMMUNITY_REPORTED" for i in url_scan2.json()["indicators"])

    # 3. User 1 submits a SECOND report for the same URL (same user reporting twice)
    rep1_dup = client.post(
        "/api/reports",
        json={"scam_type": "link", "content": "Second report from same user", "scammer_url": target_url},
        headers=h_u1,
    )
    assert rep1_dup.status_code == 201

    # Distinct users is still 1 -> Still no COMMUNITY_REPORTED indicator
    url_scan3 = client.post("/api/analyze/url", json={"url": target_url, "save": False}, headers=h_scanner)
    assert url_scan3.status_code == 200
    assert not any(i["code"] == "COMMUNITY_REPORTED" for i in url_scan3.json()["indicators"])

    # 4. User 2 (different user) submits a report for target_url
    rep2 = client.post(
        "/api/reports",
        json={"scam_type": "link", "content": "User 2 seeing same phishing link", "scammer_url": target_url},
        headers=h_u2,
    )
    assert rep2.status_code == 201

    # Now 2 DIFFERENT users have reported target_url!
    url_scan4 = client.post("/api/analyze/url", json={"url": target_url, "save": False}, headers=h_scanner)
    assert url_scan4.status_code == 200
    indicators = url_scan4.json()["indicators"]
    community_ind = next((i for i in indicators if i["code"] == "COMMUNITY_REPORTED"), None)
    assert community_ind is not None, "COMMUNITY_REPORTED indicator must be present after 2+ users"
    assert community_ind["severity"] == "medium"
    assert community_ind["weight"] == 0.4
    assert "Reported by 2 GARUDA users" in community_ind["label"]

    # Verify anonymity: Never reveal who reported (no user emails or UUIDs)
    evidence_str = str(community_ind.get("evidence", ""))
    label_str = str(community_ind.get("label", ""))
    assert "community_user1" not in evidence_str
    assert "community_user2" not in evidence_str
    assert "community_user1" not in label_str
    assert "community_user2" not in label_str

    # 5. Test with phone & UPI in message analysis
    # Both User 1 and User 2 report phone and UPI
    client.post(
        "/api/reports",
        json={
            "scam_type": "sms",
            "content": "Report with phone and UPI",
            "scammer_phone": target_phone,
            "scammer_upi": target_upi,
        },
        headers=h_u1,
    )
    client.post(
        "/api/reports",
        json={
            "scam_type": "whatsapp",
            "content": "User 2 reporting same scammer details",
            "scammer_phone": target_phone,
            "scammer_upi": target_upi,
        },
        headers=h_u2,
    )

    msg_payload = f"Call officer at {target_phone} immediately and pay arrears to {target_upi}"
    msg_scan = client.post(
        "/api/analyze/message",
        json={"text": msg_payload, "save": False},
        headers=h_scanner,
    )
    assert msg_scan.status_code == 200
    msg_indicators = msg_scan.json()["indicators"]
    msg_community_ind = next((i for i in msg_indicators if i["code"] == "COMMUNITY_REPORTED"), None)
    assert msg_community_ind is not None
    assert msg_community_ind["severity"] == "medium"
    assert msg_community_ind["weight"] == 0.4
    assert "Reported by 2 GARUDA users" in msg_community_ind["label"]
