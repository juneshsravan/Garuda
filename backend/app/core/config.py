from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_db_url(url: Optional[str]) -> str:
    """
    Normalizes PostgreSQL connection strings to SQLAlchemy + Psycopg 3 format.
    Ensures sslmode=require for remote hosts (e.g. Supabase), while allowing local connections.
    Enforces PostgreSQL only. SQLite fallback is strictly prohibited.
    """
    if not url or not url.strip():
        return ""
    
    url = url.strip()

    # Rule: PostgreSQL only. If someone tries to pass sqlite, crash immediately.
    if url.startswith("sqlite"):
        raise ValueError(
            "SQLite is strictly prohibited per GARUDA architecture rules. "
            "PostgreSQL only."
        )

    # Convert schemes to postgresql+psycopg://
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    elif url.startswith("postgresql+psycopg2://"):
        url = "postgresql+psycopg://" + url[len("postgresql+psycopg2://"):]
    elif not url.startswith("postgresql+psycopg://"):
        raise ValueError(
            f"Invalid database URL scheme. PostgreSQL is required, got: {url.split('://')[0] if '://' in url else url}. "
            "PostgreSQL only."
        )

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    is_local = hostname in ("localhost", "127.0.0.1", "")

    # For remote hosts (e.g. Supabase pooler), ensure sslmode=require if not specified
    if not is_local:
        qs = parse_qs(parsed.query)
        if "sslmode" not in qs:
            qs["sslmode"] = ["require"]
            new_query = urlencode(qs, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            return urlunparse(new_parsed)

    return url


class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    DATABASE_URL: str = ""
    TEST_DATABASE_URL: str = ""

    JWT_SECRET: str = "change_me_to_at_least_64_characters_long_secret_key_garuda_2026_secure"
    JWT_ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7
    COOKIE_SECURE: bool = False

    RATE_LIMIT_ANALYZE: str = "30/minute"
    MAX_QR_UPLOAD_MB: int = 5

    EMAIL_VERIFICATION_REQUIRED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    # Locate backend/.env whether run from backend/ or project root
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            "backend/.env",
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v:
            return normalize_db_url(v)
        return v

    @field_validator("TEST_DATABASE_URL", mode="after")
    @classmethod
    def validate_test_database_url(cls, v: str) -> str:
        if v:
            return normalize_db_url(v)
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.API_CORS_ORIGINS.split(",") if origin.strip()]

    def get_effective_database_url(self, is_test: bool = False) -> str:
        target = self.TEST_DATABASE_URL if is_test else self.DATABASE_URL
        if not target:
            env_name = "TEST_DATABASE_URL" if is_test else "DATABASE_URL"
            raise RuntimeError(
                f"{env_name} is not set in backend/.env. "
                "GARUDA requires a valid PostgreSQL connection string. "
                "SQLite or non-PostgreSQL fallback is strictly prohibited."
            )
        return target


settings = Settings()
