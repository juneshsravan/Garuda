import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.scan import AnalysisResult, Scan
from app.schemas.dashboard import (
    CategoryCount,
    DailyScanCount,
    DashboardRecentScan,
    DashboardStatsResponse,
)
from app.services.scan_service import CATEGORY_LABELS, RISK_LABELS


def get_user_dashboard_stats(db: Session, user_id: uuid.UUID) -> DashboardStatsResponse:
    """
    Computes aggregated security telemetry for the authenticated user only.
    Adheres strictly to ARCHITECTURE Sections 6 and 7:
    - total_scans, threats_detected (high + critical), suspicious (suspicious + medium), likely_safe
    - risk_distribution (count per level)
    - scans_per_day for the last 14 days
    - top_categories (top 5 with counts)
    - recent_scans (latest 5: id, scan_type, preview, risk score/level, created_at)
    """
    # 1. Total scans
    total_scans = db.scalar(
        select(func.count(Scan.id)).where(Scan.user_id == user_id)
    ) or 0

    # 2. Risk distribution & aggregate severity counts
    risk_rows = db.execute(
        select(AnalysisResult.risk_level, func.count(AnalysisResult.id))
        .join(Scan, Scan.id == AnalysisResult.scan_id)
        .where(Scan.user_id == user_id)
        .group_by(AnalysisResult.risk_level)
    ).all()

    risk_distribution: Dict[str, int] = {
        "likely_safe": 0,
        "suspicious": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
        "unable_to_verify": 0,
    }
    for level, count in risk_rows:
        risk_distribution[level] = count

    threats_detected = risk_distribution.get("high", 0) + risk_distribution.get("critical", 0)
    suspicious = risk_distribution.get("suspicious", 0) + risk_distribution.get("medium", 0)
    likely_safe = risk_distribution.get("likely_safe", 0)

    # 3. Scans per day for the last 14 days (inclusive of today UTC)
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()
    start_date = today_utc - timedelta(days=13)  # 14 days window: [today - 13, ..., today]
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    daily_rows = db.execute(
        select(
            func.date(Scan.created_at).label("scan_date"),
            func.count(Scan.id).label("scan_count"),
        )
        .where(
            Scan.user_id == user_id,
            Scan.created_at >= start_datetime,
        )
        .group_by(func.date(Scan.created_at))
    ).all()

    day_counts: Dict[str, int] = {}
    for r_date, r_count in daily_rows:
        day_counts[str(r_date)] = r_count

    scans_per_day: List[DailyScanCount] = []
    for day_offset in range(14):
        target_day = (start_date + timedelta(days=day_offset)).isoformat()
        scans_per_day.append(
            DailyScanCount(
                date=target_day,
                count=day_counts.get(target_day, 0),
            )
        )

    # 4. Top 5 categories with counts
    cat_rows = db.execute(
        select(
            AnalysisResult.category,
            func.count(AnalysisResult.id).label("cat_count"),
        )
        .join(Scan, Scan.id == AnalysisResult.scan_id)
        .where(Scan.user_id == user_id)
        .group_by(AnalysisResult.category)
        .order_by(text("cat_count DESC"))
        .limit(5)
    ).all()

    top_categories: List[CategoryCount] = []
    for cat_code, count in cat_rows:
        label = CATEGORY_LABELS.get(cat_code, cat_code.replace("_", " ").title())
        top_categories.append(
            CategoryCount(
                code=cat_code,
                label=label,
                count=count,
            )
        )

    # 5. Recent scans (latest 5)
    recent_query = (
        select(Scan)
        .where(Scan.user_id == user_id)
        .options(
            joinedload(Scan.analysis_result),
            joinedload(Scan.message),
            selectinload(Scan.urls),
            selectinload(Scan.qr_codes),
        )
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .limit(5)
    )
    recent_records = db.execute(recent_query).scalars().unique().all()

    recent_scans: List[DashboardRecentScan] = []
    for s in recent_records:
        res = s.analysis_result
        preview: Optional[str] = None
        if s.message and s.message.content:
            preview = s.message.content[:120]
        elif s.urls and len(s.urls) > 0:
            preview = s.urls[0].raw_url[:120]
        elif s.qr_codes and len(s.qr_codes) > 0:
            preview = s.qr_codes[0].payload[:120]

        score = res.risk_score if res else 0
        level = res.risk_level if res else "unable_to_verify"
        base_label = RISK_LABELS.get(level, level.replace("_", " ").title())
        label = f"{score} {base_label}" if res else base_label

        recent_scans.append(
            DashboardRecentScan(
                id=s.id,
                scan_type=s.scan_type,
                preview=preview or f"[{s.scan_type.upper()}] Scan",
                risk_score=score,
                risk_level=level,
                risk_label=label,
                created_at=s.created_at,
            )
        )

    return DashboardStatsResponse(
        total_scans=total_scans,
        threats_detected=threats_detected,
        suspicious=suspicious,
        likely_safe=likely_safe,
        risk_distribution=risk_distribution,
        scans_per_day=scans_per_day,
        top_categories=top_categories,
        recent_scans=recent_scans,
    )
