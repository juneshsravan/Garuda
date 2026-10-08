import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppException
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.scan import AnalysisResponse, ScanListResponse
from app.services.scan_service import (
    delete_scan_by_id,
    get_scan_by_id,
    get_user_scans,
)

router = APIRouter(prefix="/scans", tags=["Scans & History"])


@router.get(
    "",
    response_model=ScanListResponse,
    summary="List user's scans",
    description="Returns authenticated user's scans, newest first, with cursor pagination and filters.",
)
def list_scans(
    limit: int = Query(default=20, ge=1, le=100, description="Page limit (1-100)"),
    cursor: Optional[str] = Query(default=None, description="Opaque cursor for pagination"),
    scan_type: Optional[str] = Query(default=None, description="Filter by scan type: message | url | qr | image"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level: likely_safe | suspicious | medium | high | critical | unable_to_verify"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns only the current user's scans with cursor pagination (?limit=&cursor=)
    and optional filters for scan_type and risk_level.
    """
    items, next_cursor, has_more = get_user_scans(
        db=db,
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
        scan_type=scan_type,
        risk_level=risk_level,
    )
    return ScanListResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/{id}",
    response_model=AnalysisResponse,
    summary="Get scan details",
    description="Returns full saved analysis. Returns 404 if scan belongs to another user (no IDOR).",
)
def get_scan(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full saved analysis for scan {id}.
    Returns 404 NOT_FOUND if scan is not found or belongs to another user (prevents IDOR).
    """
    try:
        scan_uuid = uuid.UUID(id)
    except ValueError:
        raise AppException(
            code="NOT_FOUND",
            message="Scan not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return get_scan_by_id(
        db=db,
        user_id=current_user.id,
        scan_id=scan_uuid,
    )


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete scan",
    description="Deletes authenticated user's scan and all associated records. Returns 404 if scan belongs to another user.",
)
def delete_scan(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes the user's own scan and all linked records (messages, analysis results, threat indicators, urls).
    Returns 404 NOT_FOUND if scan is not found or belongs to another user (prevents IDOR).
    """
    try:
        scan_uuid = uuid.UUID(id)
    except ValueError:
        raise AppException(
            code="NOT_FOUND",
            message="Scan not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    delete_scan_by_id(
        db=db,
        user_id=current_user.id,
        scan_id=scan_uuid,
    )
    return MessageResponse(message="Scan deleted successfully.")
