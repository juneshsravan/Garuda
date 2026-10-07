import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base

# Ensure tests ONLY run against TEST_DATABASE_URL
test_db_url = settings.get_effective_database_url(is_test=True)
assert "test" in test_db_url.lower(), f"Safety check failed: TEST_DATABASE_URL must contain 'test', got {test_db_url}"

test_engine = create_engine(test_db_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def verify_test_database():
    """Confirms we are operating solely on the test database."""
    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT current_database();")).scalar()
        assert "test" in str(res).lower(), f"Expected test database, connected to: {res}"


@pytest.fixture(autouse=True)
def clean_test_tables():
    """Wipes test tables before each test to ensure test isolation."""
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs, sessions, users CASCADE;"))
    yield
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs, sessions, users CASCADE;"))


@pytest.fixture
def db():
    """Provides a database session for test verification."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provides a TestClient with get_db overridden to use TEST_DATABASE_URL."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
