import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    client = httpx.Client(base_url="http://localhost:8000")

    # 1. Health check
    health_resp = client.get("/api/health")
    print(f"1. GET /api/health -> Status: {health_resp.status_code}, Body: {health_resp.json()}")

    # 2. Docs check
    docs_resp = client.get("/docs")
    print(f"2. GET /docs -> Status: {docs_resp.status_code} (Interactive OpenAPI UI Available)")

    # 3. Register user on local garuda DB
    reg_payload = {
        "email": "junesh@garuda.ai",
        "password": "GarudaPassword2026!",
        "full_name": "Junesh Sravan"
    }
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    print(f"3. POST /api/auth/register -> Status: {reg_resp.status_code}")
    if reg_resp.status_code == 201:
        print(f"   Registered successfully: {reg_resp.json()['user']}")
    elif reg_resp.status_code == 409:
        print(f"   User already exists in database (status 409)")

    # 4. Login
    login_payload = {
        "email": "junesh@garuda.ai",
        "password": "GarudaPassword2026!"
    }
    login_resp = client.post("/api/auth/login", json=login_payload)
    print(f"4. POST /api/auth/login -> Status: {login_resp.status_code}")
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    print(f"   Access Token: {access_token[:35]}... (TTL: 15 min)")
    print(f"   Refresh Cookie: {login_resp.cookies.get('refresh_token')[:25]}... (httpOnly, SameSite=Lax)")

    # 5. /me with access token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    print(f"5. GET /api/auth/me -> Status: {me_resp.status_code}")
    print(f"   User Profile: {me_resp.json()['user']}")
    assert me_resp.status_code == 200

    # 6. Verify row directly in local DEV database (garuda)
    dev_engine = create_engine(settings.DATABASE_URL)
    with dev_engine.connect() as conn:
        row = conn.execute(text("""
            SELECT u.id, u.email, u.full_name, u.role, u.password_hash, u.created_at,
                   count(s.id) as session_count
            FROM users u
            LEFT JOIN sessions s ON s.user_id = u.id
            WHERE u.email = 'junesh@garuda.ai'
            GROUP BY u.id, u.email, u.full_name, u.role, u.password_hash, u.created_at
        """)).fetchone()
        
        print("\n" + "=" * 80)
        print("DATABASE CONFIRMATION (DIRECT QUERY IN LOCAL 'garuda' DATABASE)")
        print("=" * 80)
        print(f"User ID      : {row[0]}")
        print(f"Email        : {row[1]}")
        print(f"Full Name    : {row[2]}")
        print(f"Role         : {row[3]}")
        print(f"Argon2 Hash  : {row[4][:36]}...")
        print(f"Created At   : {row[5]}")
        print(f"Sessions     : {row[6]} active session(s)")

        audit_rows = conn.execute(text("""
            SELECT action, entity_type, created_at, metadata
            FROM audit_logs
            WHERE metadata->>'email' = 'junesh@garuda.ai'
            ORDER BY created_at DESC
        """)).fetchall()
        print("\nAudit Logs in 'garuda' DB:")
        for a in audit_rows:
            print(f"  [{a[2]}] Action: {a[0]:<12} | Entity: {a[1]:<6} | Metadata: {a[3]}")
        print("=" * 80)

if __name__ == "__main__":
    main()
