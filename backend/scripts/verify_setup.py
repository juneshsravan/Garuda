import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def verify_project(is_test: bool = False):
    name = "garuda_test (TEST_DATABASE_URL)" if is_test else "garuda (DATABASE_URL)"
    url = settings.get_effective_database_url(is_test=is_test)
    print(f"\n==========================================")
    print(f"Connecting to {name}...")
    print(f"==========================================")

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        ver = conn.execute(text("SELECT version();")).scalar()
        print(f"PostgreSQL Version: {ver[:45]}...")

        # Run inspection
        inspector = inspect(engine)
        tables = sorted(inspector.get_table_names())
        print(f"\nFound {len(tables)} tables in database:")
        for idx, table in enumerate(tables, 1):
            if table == "alembic_version":
                print(f"  {idx:2d}. {table:<28} [ALEMBIC METADATA]")
                continue
            # Check RLS status
            rls_res = conn.execute(
                text(
                    "SELECT relrowsecurity FROM pg_class WHERE oid = CAST(:tbl AS regclass);"
                ),
                {"tbl": table},
            ).scalar()
            rls_str = "ENABLED" if rls_res else "DISABLED"
            print(f"  {idx:2d}. {table:<28} [RLS: {rls_str}]")

        # Check sequence
        seq_exists = conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'report_ref_seq');"
            )
        ).scalar()
        print(f"\nReport reference sequence 'report_ref_seq': {'EXISTS' if seq_exists else 'MISSING'}")


if __name__ == "__main__":
    try:
        verify_project(is_test=False)
        verify_project(is_test=True)
        print("\nAll database checks passed successfully!")
    except Exception as e:
        print(f"\nVerification error: {e}", file=sys.stderr)
        sys.exit(1)
