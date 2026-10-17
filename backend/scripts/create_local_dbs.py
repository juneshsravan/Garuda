import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from dotenv import dotenv_values
import psycopg
from psycopg import sql

def get_admin_url() -> str:
    env_paths = [
        Path(__file__).resolve().parent.parent / ".env",
        Path(".env"),
        Path("backend/.env"),
    ]
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        for p in env_paths:
            if p.exists():
                values = dotenv_values(str(p))
                if values.get("DATABASE_URL"):
                    db_url = values["DATABASE_URL"]
                    break
    if not db_url:
        db_url = "postgresql://postgres:postgres@localhost:5432/garuda"

    parsed = urlparse(db_url)
    return urlunparse(parsed._replace(path="/postgres"))

def ensure_database(db_name: str):
    admin_url = get_admin_url()
    conn = psycopg.connect(admin_url, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
    conn.close()

if __name__ == "__main__":
    ensure_database("garuda")
    ensure_database("garuda_test")

