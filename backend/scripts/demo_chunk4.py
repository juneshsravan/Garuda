import json
import sys
from pathlib import Path
import urllib.request
import urllib.parse

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import create_engine, text
from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def run_demo():
    print("=" * 80)
    print("GARUDA CHUNK 4 DEMO (/docs API Flow)")
    print("=" * 80)

    # 1. Register
    email = "rajesh.kumar@example.com"
    reg_payload = {
        "email": email,
        "password": "SecurePassword2026!",
        "full_name": "Rajesh Kumar",
    }
    print(f"\n1. POST /api/auth/register (Registering {email})...")
    status, reg_res = request("POST", "/api/auth/register", reg_payload)
    if status == 409:
        print("   User already exists, logging in directly...")
        # Login
        status, login_res = request("POST", "/api/auth/login", {"email": email, "password": "SecurePassword2026!"})
        token = login_res["access_token"]
        user_id = login_res["user"]["id"]
    else:
        assert status == 201, f"Register failed: {reg_res}"
        token = reg_res["access_token"]
        user_id = reg_res["user"]["id"]
        print(f"   Status: {status} Created")
        print(f"   User ID: {user_id}")
        print(f"   email_verified_at: {reg_res['user']['email_verified_at']} (Correctly None)")

    # 2. Login verification
    print(f"\n2. POST /api/auth/login...")
    status, login_res = request("POST", "/api/auth/login", {"email": email, "password": "SecurePassword2026!"})
    assert status == 200, f"Login failed: {login_res}"
    print(f"   Status: {status} OK")
    print(f"   Bearer Access Token obtained (valid 15m)")

    # 3. Analyze Message (Save=True)
    msg_text = (
        "Income Tax Dept: You are eligible for a refund of ₹15,490. "
        "Submit your bank details at http://incometax-refund.co.in-claim.top"
    )
    print(f"\n3. POST /api/analyze/message (Analyzing suspicious message, save=True)...")
    print(f"   Text: \"{msg_text}\"")
    status, analyze_res = request("POST", "/api/analyze/message", {"text": msg_text, "save": True}, token=token)
    assert status == 200, f"Analyze failed: {analyze_res}"
    scan_id = analyze_res["scan_id"]
    print(f"   Status: {status} OK")
    print(f"   Scan ID: {scan_id}")
    print(f"   Risk: Score={analyze_res['risk']['score']}, Level={analyze_res['risk']['level']} ({analyze_res['risk']['label']})")
    print(f"   Category: {analyze_res['category']['code']} - {analyze_res['category']['label']}")
    print(f"   Confidence: {analyze_res['confidence']}")
    print(f"   Indicators Detected: {len(analyze_res['indicators'])}")
    for ind in analyze_res["indicators"]:
        print(f"     * [{ind['severity'].upper()}] {ind['code']}: {ind['label']} (evidence: {ind['evidence']})")
    print(f"   Extracted URLs: {len(analyze_res['extracted']['urls'])}")
    for u in analyze_res["extracted"]["urls"]:
        print(f"     * {u['raw']} (Domain: {u['domain']}, Deceptive: {u.get('is_deceptive')})")

    # 4. List Scans
    print(f"\n4. GET /api/scans (Listing current user's scans with cursor pagination)...")
    status, list_res = request("GET", "/api/scans?limit=5", token=token)
    assert status == 200, f"List scans failed: {list_res}"
    print(f"   Status: {status} OK")
    print(f"   Total items returned in page: {len(list_res['items'])}")
    print(f"   has_more: {list_res['has_more']}")
    for item in list_res["items"]:
        print(f"     - Scan ID: {item['id']}")
        print(f"       Type: {item['scan_type']} | Status: {item['status']}")
        print(f"       Risk: {item['risk']['level']} ({item['risk']['score']}/100)")
        print(f"       Preview: {item['content_preview'][:60]}...")

    # 5. Get Scan by ID
    print(f"\n5. GET /api/scans/{scan_id} (Opening scan details)...")
    status, detail_res = request("GET", f"/api/scans/{scan_id}", token=token)
    assert status == 200, f"Get scan failed: {detail_res}"
    print(f"   Status: {status} OK")
    print(f"   Scan ID: {detail_res['scan_id']}")
    print(f"   Summary: {detail_res['summary']}")
    print(f"   Recommendations: {detail_res['recommendations']}")
    print(f"   Verify Steps: {detail_res['verify_steps']}")

    # 6. Verify Local PostgreSQL Database (garuda)
    print("\n" + "=" * 80)
    print("LOCAL POSTGRESQL DATABASE (garuda) VERIFICATION")
    print("=" * 80)
    engine_dev = create_engine(settings.DATABASE_URL)
    with engine_dev.connect() as conn:
        print("\n--- Table: users ---")
        users = conn.execute(
            text("SELECT id, email, full_name, role, is_active, email_verified_at, created_at FROM users WHERE email = :e"),
            {"e": email}
        ).mappings().all()
        for u in users:
            print(dict(u))

        print("\n--- Table: scans ---")
        scans = conn.execute(
            text("SELECT id, user_id, scan_type, status, input_sha256, persisted_content, created_at FROM scans WHERE id = :s"),
            {"s": scan_id}
        ).mappings().all()
        for s in scans:
            print(dict(s))

        print("\n--- Table: messages ---")
        messages = conn.execute(
            text("SELECT id, scan_id, content, detected_language FROM messages WHERE scan_id = :s"),
            {"s": scan_id}
        ).mappings().all()
        for m in messages:
            print(dict(m))

        print("\n--- Table: analysis_results ---")
        ar = conn.execute(
            text("SELECT id, scan_id, risk_score, risk_level, confidence, category, summary, legitimacy_signals FROM analysis_results WHERE scan_id = :s"),
            {"s": scan_id}
        ).mappings().all()
        for a in ar:
            print(dict(a))

        print("\n--- Table: threat_indicators ---")
        ti = conn.execute(
            text("SELECT id, analysis_id, code, label, severity, weight, evidence FROM threat_indicators WHERE analysis_id = :aid"),
            {"aid": ar[0]["id"]} if ar else {"aid": None}
        ).mappings().all()
        for t in ti:
            print(dict(t))

        print("\n--- Table: urls ---")
        urls = conn.execute(
            text("SELECT id, scan_id, raw_url, normalized_url, registered_domain, source FROM urls WHERE scan_id = :s"),
            {"s": scan_id}
        ).mappings().all()
        for u in urls:
            print(dict(u))

    print("\n" + "=" * 80)
    print("DEMO & DATABASE VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
