import uuid
from datetime import datetime, timezone
import pytest

from app.models.scan import AnalysisResult, Message, Scan


_ip_seed = 100


def register_user_token(client, email: str) -> tuple[str, dict]:
    global _ip_seed
    _ip_seed += 1
    headers = {"X-Forwarded-For": f"203.0.113.{_ip_seed}"}
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Dashboard Tester",
    }
    resp = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]


def test_dashboard_stats_unauthenticated_rejected(client):
    """Rule: Unauthenticated requests to /api/dashboard/stats must be rejected with 401."""
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 401
    err = resp.json()["error"]
    assert err["code"] in ["UNAUTHORIZED", "INVALID_AUTH_HEADER"]


def test_dashboard_stats_empty_for_new_user(client):
    """Rule: A newly registered user with 0 scans receives empty/zero metrics and 14 empty daily slots."""
    token, _ = register_user_token(client, "empty.dashboard@example.com")
    resp = client.get(
        "/api/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_scans"] == 0
    assert data["threats_detected"] == 0
    assert data["suspicious"] == 0
    assert data["likely_safe"] == 0
    assert data["risk_distribution"] == {
        "likely_safe": 0,
        "suspicious": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
        "unable_to_verify": 0,
    }
    assert len(data["scans_per_day"]) == 14
    for day_slot in data["scans_per_day"]:
        assert day_slot["count"] == 0
    assert data["top_categories"] == []
    assert data["recent_scans"] == []


def test_dashboard_stats_correct_counts_and_user_isolation(client, db):
    """
    Rule: GET /api/dashboard/stats calculates exact metrics (high+critical threats,
    suspicious+medium, likely_safe, 14 days activity, top 5 categories, 5 recent scans)
    and strictly isolates data so other users' scans are not included.
    """
    token_a, user_a = register_user_token(client, "analyst.a@example.com")
    token_b, user_b = register_user_token(client, "analyst.b@example.com")

    user_a_id = uuid.UUID(user_a["id"])
    user_b_id = uuid.UUID(user_b["id"])

    # Create scans for User A:
    # 1. Critical risk scan (financial_fraud)
    # 2. High risk scan (phishing)
    # 3. Medium risk scan (utility_impersonation)
    # 4. Suspicious scan (fake_job_investment)
    # 5. Likely safe scan (legitimate_advisory)
    # 6. Another Critical scan (financial_fraud)
    scans_a_config = [
        ("financial_fraud", "critical", 95, "Urgent: UPI Collect request for ₹50,000 from unknown sender"),
        ("phishing", "high", 88, "Dear customer, your PAN is blocked. Update at http://fake-kyc.in"),
        ("utility_impersonation", "medium", 55, "Power will be cut off at 9:30 PM call 9000000001"),
        ("fake_job_investment", "suspicious", 35, "Earn ₹5000/day liking YouTube videos on Telegram"),
        ("legitimate_advisory", "likely_safe", 10, "RBI Kehta Hai: Never share OTP or passwords"),
        ("financial_fraud", "critical", 92, "Scan QR to receive ₹2000 refund directly to bank"),
    ]

    for cat, level, score, text_content in scans_a_config:
        s_id = uuid.uuid4()
        scan = Scan(
            id=s_id,
            user_id=user_a_id,
            scan_type="message",
            status="done",
            persisted_content=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(scan)
        db.flush()

        msg = Message(
            id=uuid.uuid4(),
            scan_id=s_id,
            content=text_content,
        )
        db.add(msg)

        res = AnalysisResult(
            id=uuid.uuid4(),
            scan_id=s_id,
            risk_score=score,
            risk_level=level,
            confidence=0.9,
            verification_status="unverified",
            category=cat,
            summary=f"Analysis for {cat}",
            legitimacy_signals=[],
            recommendations=[],
            verify_steps=[],
            intel_status=[],
            engine_version="2.0.0",
        )
        db.add(res)

    # Create 3 scans for User B (must NOT be counted in User A's stats)
    for i in range(3):
        s_b_id = uuid.uuid4()
        scan_b = Scan(
            id=s_b_id,
            user_id=user_b_id,
            scan_type="message",
            status="done",
            persisted_content=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(scan_b)
        db.flush()

        res_b = AnalysisResult(
            id=uuid.uuid4(),
            scan_id=s_b_id,
            risk_score=90,
            risk_level="high",
            confidence=0.9,
            verification_status="unverified",
            category="financial_fraud",
            summary="User B scan",
            legitimacy_signals=[],
            recommendations=[],
            verify_steps=[],
            intel_status=[],
            engine_version="2.0.0",
        )
        db.add(res_b)

    db.commit()

    # Query User A dashboard stats
    resp_a = client.get(
        "/api/dashboard/stats",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 200
    data_a = resp_a.json()

    # Verify counts for User A
    assert data_a["total_scans"] == 6
    # Threats = high (1) + critical (2) = 3
    assert data_a["threats_detected"] == 3
    # Suspicious = suspicious (1) + medium (1) = 2
    assert data_a["suspicious"] == 2
    # Likely safe = 1
    assert data_a["likely_safe"] == 1

    # Verify risk distribution
    assert data_a["risk_distribution"]["critical"] == 2
    assert data_a["risk_distribution"]["high"] == 1
    assert data_a["risk_distribution"]["medium"] == 1
    assert data_a["risk_distribution"]["suspicious"] == 1
    assert data_a["risk_distribution"]["likely_safe"] == 1
    assert data_a["risk_distribution"]["unable_to_verify"] == 0

    # Verify scans_per_day (14 days, today's entry has count 6)
    assert len(data_a["scans_per_day"]) == 14
    today_iso = datetime.now(timezone.utc).date().isoformat()
    today_slot = [slot for slot in data_a["scans_per_day"] if slot["date"] == today_iso]
    assert len(today_slot) == 1
    assert today_slot[0]["count"] == 6

    # Verify top categories
    # financial_fraud has 2, others have 1
    assert len(data_a["top_categories"]) == 5
    assert data_a["top_categories"][0]["code"] == "financial_fraud"
    assert data_a["top_categories"][0]["count"] == 2

    # Verify recent scans (capped at 5, newest first)
    assert len(data_a["recent_scans"]) == 5
    first_recent = data_a["recent_scans"][0]
    assert "id" in first_recent
    assert first_recent["scan_type"] == "message"
    assert "preview" in first_recent
    assert first_recent["risk_score"] in [92, 10, 35, 55, 88, 95]
    assert first_recent["risk_level"] in ["critical", "likely_safe", "suspicious", "medium", "high"]

    # Now verify User B only sees their own 3 scans
    resp_b = client.get(
        "/api/dashboard/stats",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["total_scans"] == 3
    assert data_b["threats_detected"] == 3
    assert data_b["suspicious"] == 0
    assert data_b["likely_safe"] == 0
