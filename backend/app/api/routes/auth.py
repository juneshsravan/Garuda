from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Header, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.errors import AppException
from app.core.rate_limit import get_client_ip, limiter
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import Session as UserSession, User
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    TokenRefreshResponse,
    UserLoginRequest,
    UserMeResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Sets the httpOnly SameSite=Lax refresh token cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.REFRESH_TTL_DAYS * 86400,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh token cookie upon logout."""
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: UserRegisterRequest,
    response: Response,
    db: DBSession = Depends(get_db),
):
    """
    Registers a new user with email, password (min 8), and full_name (min 2).
    Hashes password using Argon2id, creates session and audit log.
    """
    # Check if user already exists
    existing_user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing_user:
        raise AppException(
            code="EMAIL_ALREADY_EXISTS",
            message="A user with this email address already exists.",
            status_code=status.HTTP_409_CONFLICT,
            details={"email": ["Email is already registered."]},
        )

    # Hash password using Argon2id
    pwd_hash = hash_password(payload.password)

    user = User(
        email=payload.email,
        password_hash=pwd_hash,
        full_name=payload.full_name,
        role="user",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if not settings.EMAIL_VERIFICATION_REQUIRED else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token and refresh token
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )
    raw_refresh = generate_refresh_token()
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh),
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TTL_DAYS),
    )
    db.add(session)
    db.commit()

    # Log audit event
    log_audit(
        db=db,
        action="register",
        entity_type="user",
        actor_user_id=user.id,
        entity_id=str(user.id),
        ip=get_client_ip(request),
        metadata={"email": user.email},
    )

    _set_refresh_cookie(response, raw_refresh)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: UserLoginRequest,
    response: Response,
    db: DBSession = Depends(get_db),
):
    """
    Authenticates user. Fails with identical error for unknown email and wrong password.
    """
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        log_audit(
            db=db,
            action="failed_login",
            entity_type="user",
            actor_user_id=user.id if user else None,
            entity_id=str(user.id) if user else None,
            ip=get_client_ip(request),
            metadata={"email": payload.email, "reason": "invalid_credentials"},
        )
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppException(
            code="USER_INACTIVE",
            message="Your account has been deactivated. Please contact support.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.email_verified_at:
        raise AppException(
            code="EMAIL_NOT_VERIFIED",
            message="Email verification is required before login.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    # Issue access token
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

    # Create new session with hashed refresh token
    raw_refresh = generate_refresh_token()
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh),
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TTL_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(user)

    # Audit log
    log_audit(
        db=db,
        action="login",
        entity_type="user",
        actor_user_id=user.id,
        entity_id=str(user.id),
        ip=get_client_ip(request),
        metadata={"email": user.email},
    )

    _set_refresh_cookie(response, raw_refresh)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: DBSession = Depends(get_db),
):
    """
    Rotates refresh token and issues a new access token.
    The old refresh token session is revoked immediately.
    """
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise AppException(
            code="MISSING_REFRESH_TOKEN",
            message="Refresh token cookie is missing.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_hash = hash_token(raw_refresh)
    session = db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
        )
    ).scalar_one_or_none()

    if not session:
        raise AppException(
            code="INVALID_REFRESH_TOKEN",
            message="Invalid or revoked refresh token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    now = datetime.now(timezone.utc)
    # Check expiry
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        session.revoked_at = now
        db.commit()
        raise AppException(
            code="REFRESH_TOKEN_EXPIRED",
            message="Refresh token has expired. Please login again.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise AppException(
            code="USER_NOT_FOUND",
            message="User account is inactive or not found.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Rotation: Revoke old session and issue new one
    session.revoked_at = now
    new_raw_refresh = generate_refresh_token()
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(new_raw_refresh),
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        expires_at=now + timedelta(days=settings.REFRESH_TTL_DAYS),
    )
    db.add(new_session)
    db.commit()

    # Issue new 15 min access token
    new_access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

    _set_refresh_cookie(response, new_raw_refresh)
    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: DBSession = Depends(get_db),
):
    """
    Revokes the current session and clears the refresh cookie.
    """
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        token_hash = hash_token(raw_refresh)
        session = db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
        ).scalar_one_or_none()

        if session:
            session.revoked_at = datetime.now(timezone.utc)
            log_audit(
                db=db,
                action="logout",
                entity_type="session",
                actor_user_id=session.user_id,
                entity_id=str(session.id),
                ip=get_client_ip(request),
            )
            db.commit()

    _clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated user's current profile.
    """
    return UserMeResponse(user=UserResponse.model_validate(current_user))
