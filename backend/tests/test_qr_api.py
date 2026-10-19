"""
Tests for QR API endpoints (/api/analyze/qr, /api/analyze/qr/image)
and scan history preview.
Run with:  python -m pytest tests/test_qr_api.py -v
"""
import io
import pytest
import qrcode
from PIL import Image
from sqlalchemy import select

from app.models.scan import QRCode, Scan

_ip_counter = 100


def register_user(client, email: str = "qr_tester@example.com") -> tuple[str, dict]:
    """Helper to register a user and return the Bearer token and user dictionary."""
    global _ip_counter
    _ip_counter += 1
    headers = {"X-Forwarded-For": f"203.0.113.{_ip_counter}"}

    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "QR Tester",
    }
    resp = client.post("/api/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]


def make_qr_png_bytes(content: str) -> bytes:
    """Generates an in-memory PNG QR code using the qrcode package."""
    qr_img = qrcode.make(content)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    return buf.getvalue()


def make_blank_png_bytes(width: int = 200, height: int = 200) -> bytes:
    """Generates an in-memory blank white PNG with no QR code."""
    img = Image.new("RGB", (width, height), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. User-Specified Test Cases
# ---------------------------------------------------------------------------

def test_upi_scam_is_high(client):
    """UPI scam -> high"""
    token, _ = register_user(client, "upi_scam@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received",
        "save": True,
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "high"
    assert data["risk"]["score"] >= 65
    assert data["extracted"]["qr"]["type"] == "upi"
    assert data["extracted"]["upi"]["pa"] == "sbi.refund@ybl"
    assert "Scanning a QR code can only SEND money, never receive it." in data["recommendations"]


def test_safe_upi_is_likely_safe(client):
    """'upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar' -> likely_safe with confidence 0.5"""
    token, _ = register_user(client, "upi_safe@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
        "save": True,
        "context": None,
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "likely_safe"
    assert data["confidence"] == 0.5
    assert data["verification_status"] == "no_warning_signs_found"
    assert data["extracted"]["qr"]["type"] == "upi"
    assert data["extracted"]["upi"]["pa"] == "ramesh123@oksbi"


def test_ramesh_qr_context_receive_money_is_high(client):
    """Ramesh QR with context 'receive_money' -> high with QR_RECEIVE_MONEY_CLAIM indicator"""
    token, _ = register_user(client, "upi_rec_money@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
        "save": True,
        "context": "receive_money",
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "high"
    assert data["risk"]["score"] >= 65

    ind_codes = {i["code"]: i for i in data["indicators"]}
    assert "QR_RECEIVE_MONEY_CLAIM" in ind_codes
    ind = ind_codes["QR_RECEIVE_MONEY_CLAIM"]
    assert ind["severity"] == "high"
    assert ind["weight"] == 0.85
    assert "QR codes can only SEND money" in ind["label"]


def test_ramesh_qr_context_stranger_request_is_suspicious_or_medium(client):
    """Ramesh QR with context 'stranger_request' -> suspicious or medium with QR_STRANGER_REQUEST"""
    token, _ = register_user(client, "upi_stranger@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
        "save": True,
        "context": "stranger_request",
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] in ("suspicious", "medium")

    ind_codes = {i["code"]: i for i in data["indicators"]}
    assert "QR_STRANGER_REQUEST" in ind_codes
    ind = ind_codes["QR_STRANGER_REQUEST"]
    assert ind["severity"] == "medium"
    assert ind["weight"] == 0.4
    assert "stranger or caller" in ind["label"].lower()


def test_image_endpoint_with_context_receive_money(client):
    """Image endpoint with context 'receive_money' -> high"""
    token, _ = register_user(client, "qr_img_context@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    qr_content = "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar"
    png_bytes = make_qr_png_bytes(qr_content)

    resp = client.post(
        "/api/analyze/qr/image",
        files={"file": ("qr.png", png_bytes, "image/png")},
        data={"save": "true", "context": "receive_money"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "high"
    assert any(i["code"] == "QR_RECEIVE_MONEY_CLAIM" for i in data["indicators"])


def test_phishing_url_in_qr_is_high(client):
    """'http://sbi-kyc-update.xyz/login' -> high"""
    token, _ = register_user(client, "qr_phish@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "http://sbi-kyc-update.xyz/login",
        "save": True,
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "high"
    assert data["extracted"]["qr"]["type"] == "url"
    assert len(data["extracted"]["urls"]) > 0
    assert data["extracted"]["urls"][0]["raw"] == "http://sbi-kyc-update.xyz/login"


def test_betting_url_in_qr_is_high(client):
    """'https://indian.1xbet.com' -> high"""
    token, _ = register_user(client, "qr_betting@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "https://indian.1xbet.com",
        "save": True,
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "high"
    assert data["category"]["code"] == "illegal_betting"


def test_save_false_saves_nothing(client, db):
    """save=false saves nothing"""
    token, user = register_user(client, "nosave_qr@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
        "save": False,
    }
    resp = client.post("/api/analyze/qr", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_id"] is None

    # Check direct db: no Scan or QRCode record exists for this user
    scans = db.execute(select(Scan).where(Scan.user_id == user["id"])).scalars().all()
    assert len(scans) == 0

    qr_records = db.execute(select(QRCode).where(QRCode.payload == payload["content"])).scalars().all()
    assert len(qr_records) == 0


def test_no_login_returns_401(client):
    """no login -> 401"""
    # 1. Content endpoint
    resp1 = client.post("/api/analyze/qr", json={"content": "http://example.com", "save": False})
    assert resp1.status_code == 401

    # 2. Image endpoint
    png_bytes = make_blank_png_bytes()
    resp2 = client.post(
        "/api/analyze/qr/image",
        files={"file": ("test.png", png_bytes, "image/png")},
        data={"save": "false"},
    )
    assert resp2.status_code == 401


def test_another_user_cannot_read_scan(client):
    """another user cannot read the scan (prevents IDOR, returns 404)"""
    # User A creates a scan
    token_a, _ = register_user(client, "user_a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp = client.post(
        "/api/analyze/qr",
        json={"content": "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar", "save": True},
        headers=headers_a,
    )
    assert resp.status_code == 200
    scan_id = resp.json()["scan_id"]
    assert scan_id is not None

    # User B tries to read User A's scan
    token_b, _ = register_user(client, "user_b@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    read_resp = client.get(f"/api/scans/{scan_id}", headers=headers_b)
    assert read_resp.status_code == 404
    assert read_resp.json()["error"]["code"] == "NOT_FOUND"


def test_image_endpoint_with_generated_qr(client):
    """image endpoint with a QR PNG generated in the test (qrcode package as test dependency)"""
    token, _ = register_user(client, "qr_img_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    qr_content = "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar"
    png_bytes = make_qr_png_bytes(qr_content)

    resp = client.post(
        "/api/analyze/qr/image",
        files={"file": ("qr.png", png_bytes, "image/png")},
        data={"save": "true"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "qr"
    assert data["risk"]["level"] == "likely_safe"
    assert data["extracted"]["qr"]["content"] == qr_content
    assert data["extracted"]["qr"]["type"] == "upi"
    assert data["scan_id"] is not None


def test_blank_image_returns_qr_not_found(client):
    """blank image -> QR_NOT_FOUND (422)"""
    token, _ = register_user(client, "blank_img_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    blank_png = make_blank_png_bytes()

    resp = client.post(
        "/api/analyze/qr/image",
        files={"file": ("blank.png", blank_png, "image/png")},
        data={"save": "true"},
        headers=headers,
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "QR_NOT_FOUND"


# ---------------------------------------------------------------------------
# 2. History & Preview Tests
# ---------------------------------------------------------------------------

def test_qr_scan_history_preview(client):
    """In get_user_scans, show a preview for qr scans (decoded content, first 120 chars)"""
    token, _ = register_user(client, "history_qr_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    long_payload = "upi://pay?pa=someone123@oksbi&pn=Some%20Very%20Long%20Merchant%20Name%20That%20Exceeds%20The%20Normal%20Length%20To%20Verify%20Content%20Preview%20Truncation%20Logic%20Properly"
    resp = client.post(
        "/api/analyze/qr",
        json={"content": long_payload, "save": True},
        headers=headers,
    )
    assert resp.status_code == 200

    # Retrieve scan history list
    list_resp = client.get("/api/scans/", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) >= 1

    qr_item = next(i for i in items if i["scan_type"] == "qr")
    assert qr_item["content_preview"] is not None
    assert qr_item["content_preview"] == long_payload[:120]
    assert len(qr_item["content_preview"]) <= 120


# ---------------------------------------------------------------------------
# 3. Validation & Edge Cases
# ---------------------------------------------------------------------------

def test_invalid_qr_content_returns_422(client):
    token, _ = register_user(client, "invalid_qr@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Malformed UPI address
    resp = client.post("/api/analyze/qr", json={"content": "upi://pay?pa=abc", "save": True}, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_QR"


def test_non_image_upload_returns_422(client):
    token, _ = register_user(client, "non_img@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/analyze/qr/image",
        files={"file": ("test.txt", b"this is not an image", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_QR"


def test_plain_text_qr(client):
    token, _ = register_user(client, "plain_text@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/analyze/qr",
        json={"content": "Welcome to our store. Free Wi-Fi at counter.", "save": True},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"]["level"] == "likely_safe"
    assert data["category"]["code"] == "plain_text_qr"
    assert data["extracted"]["qr"]["type"] == "text"
