import uuid
from typing import Optional
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency: authenticates user via HTTP Bearer token.
    Exposes HTTPBearer security scheme to OpenAPI so /docs displays Authorize button and lock icons.
    """
    auth_header = request.headers.get("authorization")

    if not credentials:
        if not auth_header:
            raise AppException(
                code="UNAUTHORIZED",
                message="Authentication credentials were not provided.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AppException(
                code="INVALID_AUTH_HEADER",
                message="Invalid Authorization header format. Expected 'Bearer <token>'.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
    else:
        token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise AppException(
            code="TOKEN_EXPIRED",
            message="Access token has expired. Please refresh your session.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    except jwt.PyJWTError:
        raise AppException(
            code="INVALID_TOKEN",
            message="Could not validate credentials.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid token payload: missing subject.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid user ID format in token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = db.get(User, user_uuid)
    if not user:
        raise AppException(
            code="USER_NOT_FOUND",
            message="User associated with this token does not exist.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppException(
            code="USER_INACTIVE",
            message="User account is deactivated.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: enforces admin role on protected routes.
    """
    if current_user.role != "admin":
        raise AppException(
            code="FORBIDDEN",
            message="Admin privileges required.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return current_user
