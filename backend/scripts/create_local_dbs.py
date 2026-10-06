import psycopg
from psycopg import sql

def ensure_database(db_name: str):
    # Connect to the default postgres database
    conn = psycopg.connect("postgresql://postgres:garuda123@localhost:5432/postgres", autocommit=True)
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
