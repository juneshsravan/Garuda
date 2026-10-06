from typing import Generator, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Lazy or immediate engine creation
_engine = None
_SessionLocal = None


def get_engine(is_test: bool = False):
    global _engine, _SessionLocal
    if _engine is None or is_test:
        db_url = settings.get_effective_database_url(is_test=is_test)
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        if not is_test:
            _engine = engine
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        return engine
    return _engine


def get_session_local(is_test: bool = False) -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None or is_test:
        engine = get_engine(is_test=is_test)
        sl = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        if not is_test:
            _SessionLocal = sl
        return sl
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, Optional[str]]:
    """
    Executes a simple query against Supabase PostgreSQL to verify connection health.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:
        return False, str(exc)
