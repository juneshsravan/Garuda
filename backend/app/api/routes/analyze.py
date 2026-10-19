from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.errors import AppException
from app.core.rate_limit import get_user_rate_limit_key, limiter
from app.db.session import get_db
from app.engine.analyzers.qr_analyzer import decode_qr_image
from app.models.user import User
from app.schemas.scan import (
    AnalysisResponse,
    MessageAnalyzeRequest,
    QrAnalyzeRequest,
    UrlAnalyzeRequest,
)
from app.services.scan_service import analyze_message, analyze_qr, analyze_url

router = APIRouter(prefix="/analyze", tags=["Detection & Analysis"])


@router.post(
    "/message",
    response_model=AnalysisResponse,
    summary="Analyze SMS / chat message",
    description="Analyzes message for scam, phishing, extortion, and legitimacy signals. Requires login.",
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE, key_func=get_user_rate_limit_key)
def analyze_message_endpoint(
    request: Request,
    payload: MessageAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes message text (1-5000 chars) for scams, fraud, and phishing.
    Rate limited to 30 requests/minute per authenticated user.
    If save=True, persists scans, messages, analysis_results, threat_indicators, and urls in one transaction.
    If save=False, stores nothing.
    """
    return analyze_message(
        db=db,
        user_id=current_user.id,
        text=payload.text,
        save=payload.save,
    )


@router.post(
    "/url",
    response_model=AnalysisResponse,
    summary="Analyze a web link (URL)",
    description=(
        "Checks a link for phishing, fake brand look-alikes, illegal betting and adult sites "
        "using static analysis only (the link is never opened). Requires login."
    ),
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE, key_func=get_user_rate_limit_key)
def analyze_url_endpoint(
    request: Request,
    payload: UrlAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes a URL with GARUDA's static URL analyzer.
    Invalid input returns 422 (INVALID_URL) and nothing is saved.
    If save=True, persists scans (scan_type=url), urls, analysis_results and threat_indicators.
    If save=False, stores nothing.
    """
    return analyze_url(
        db=db,
        user_id=current_user.id,
        url=payload.url,
        save=payload.save,
    )


@router.post(
    "/qr",
    response_model=AnalysisResponse,
    summary="Analyze decoded QR payload",
    description=(
        "Analyzes decoded QR text (UPI payment, web link, or plain text) "
        "using static analysis without visiting destinations. Requires login."
    ),
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE, key_func=get_user_rate_limit_key)
def analyze_qr_endpoint(
    request: Request,
    payload: QrAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes a QR code payload.
    Invalid input returns 422 (INVALID_QR) and nothing is saved.
    If save=True, persists scans (scan_type=qr), qr_codes, analysis_results and threat_indicators.
    If save=False, stores nothing.
    """
    return analyze_qr(
        db=db,
        user_id=current_user.id,
        content=payload.content,
        save=payload.save,
        context=payload.context,
    )


@router.post(
    "/qr/image",
    response_model=AnalysisResponse,
    summary="Decode and analyze QR code image",
    description=(
        "Decodes a QR code from an uploaded image in-memory and analyzes the payload. "
        "Rejects images over 5 MB. Image is never saved to disk. Requires login."
    ),
)
@limiter.limit(settings.RATE_LIMIT_ANALYZE, key_func=get_user_rate_limit_key)
async def analyze_qr_image_endpoint(
    request: Request,
    file: UploadFile = File(...),
    save: bool = Form(default=True),
    context: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Decodes and analyzes an in-memory QR code image upload.
    No QR code found returns 422 (QR_NOT_FOUND).
    If save=True, persists scans (scan_type=qr), qr_codes, analysis_results and threat_indicators.
    If save=False, stores nothing.
    """
    file_bytes = await file.read()
    try:
        content = decode_qr_image(file_bytes)
    except ValueError as e:
        raise AppException(
            code="INVALID_QR",
            message=str(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if not content:
        raise AppException(
            code="QR_NOT_FOUND",
            message="No QR code found in the uploaded image.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    clean_context = None if not context or context.strip() in ("", "null", "none") else context.strip()
    if clean_context and clean_context not in ("known_payee", "receive_money", "stranger_request"):
        raise AppException(
            code="INVALID_CONTEXT",
            message="Invalid context value. Must be 'known_payee', 'receive_money', or 'stranger_request'.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return analyze_qr(
        db=db,
        user_id=current_user.id,
        content=content,
        save=save,
        context=clean_context,
    )