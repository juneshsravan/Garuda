import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import get_user_rate_limit_key, limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import (
    create_report,
    get_report_by_id,
    get_user_reports,
)

router = APIRouter(prefix="/reports", tags=["Report Center"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a scam / fraud incident report",
    description=(
        "Registers an incident report with GARUDA for telemetry and community safety. "
        "Filing this report does not lodge a police complaint or government FIR on your behalf. "
        "Requires login."
    ),
)
@limiter.limit("20/minute", key_func=get_user_rate_limit_key)
def create_report_endpoint(
    request: Request,
    payload: ReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a new incident report to GARUDA.
    Rate limited to 20 submissions per minute per user.
    """
    report = create_report(db=db, user_id=current_user.id, payload=payload)
    return report


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List your own incident reports",
    description="Returns all reports submitted by the authenticated user, newest first. Requires login.",
)
@limiter.limit("60/minute", key_func=get_user_rate_limit_key)
def list_reports_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all reports filed by the calling user. Strictly own reports only."""
    items = get_user_reports(db=db, user_id=current_user.id)
    return ReportListResponse(items=items, total=len(items))


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get single incident report by ID",
    description="Returns full report details for own report. Returns 404 for other users' reports.",
)
@limiter.limit("60/minute", key_func=get_user_rate_limit_key)
def get_report_endpoint(
    request: Request,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a report dossier by ID.
    Enforces strict ownership: other users receive 404 (IDOR prevention).
    """
    return get_report_by_id(db=db, user_id=current_user.id, report_id=report_id)
