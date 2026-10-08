from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import jwt

from app.core.errors import format_error_response


def get_client_ip(request: Request) -> str:
    """Extracts client IP from X-Forwarded-For header or direct client host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_user_rate_limit_key(request: Request) -> str:
    """
    Extracts authenticated user ID from Authorization Bearer token.
    Falls back to client IP if token is absent or invalid.
    Enforces per-user rate limiting (e.g. 30/min/user).
    """
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    return get_client_ip(request)


# Global in-memory rate limiter
limiter = Limiter(key_func=get_client_ip, default_limits=[])


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Formats rate limit exceeded errors to standard GARUDA error contract."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=format_error_response(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please wait a minute before trying again.",
            details={
                "limit": str(exc.detail),
            },
        ),
    )
