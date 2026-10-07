import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# Initialize Argon2 password hasher
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plain_password: str) -> str:
    """Hashes a password using Argon2id."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    return _password_hash.verify(plain_password, hashed_password)


def generate_refresh_token() -> str:
    """Generates a cryptographically strong random refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Computes SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token valid for 15 minutes by default.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TTL_MIN)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises jwt.PyJWTError subclasses (ExpiredSignatureError, InvalidTokenError, etc.) on failure.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
