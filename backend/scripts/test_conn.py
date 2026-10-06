import sys
from pathlib import Path
from sqlalchemy import create_engine, text

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings

def test():
    print("Testing DEV DB connection...", flush=True)
    engine_dev = create_engine(settings.DATABASE_URL, connect_args={"connect_timeout": 15})
    with engine_dev.connect() as conn:
        ver = conn.execute(text("SELECT version();")).scalar()
        print(f"DEV connected! PostgreSQL Version: {ver[:45]}", flush=True)

    print("\nTesting TEST DB connection...", flush=True)
    engine_test = create_engine(settings.TEST_DATABASE_URL, connect_args={"connect_timeout": 15})
    with engine_test.connect() as conn:
        ver = conn.execute(text("SELECT version();")).scalar()
        print(f"TEST connected! PostgreSQL Version: {ver[:45]}", flush=True)

if __name__ == "__main__":
    test()
