from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import get_user_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get user dashboard telemetry",
    description="Returns aggregated metrics, 14-day scan volume, risk distribution, top categories, and recent scans for the authenticated user only.",
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns security telemetry restricted strictly to the authenticated user:
    - total_scans, threats_detected, suspicious, likely_safe
    - risk_distribution, scans_per_day (14 days), top_categories (top 5), recent_scans (latest 5)
    """
    return get_user_dashboard_stats(db=db, user_id=current_user.id)
