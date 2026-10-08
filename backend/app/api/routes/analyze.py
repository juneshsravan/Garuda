from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import get_user_rate_limit_key, limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.scan import AnalysisResponse, MessageAnalyzeRequest
from app.services.scan_service import analyze_message

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
