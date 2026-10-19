import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.models.report import Report, ReportStatusHistory
from app.schemas.report import ReportCreateRequest


def normalize_phone_digits(phone: Optional[str]) -> Optional[str]:
    """Extracts trailing 10 digits for standardized Indian phone comparison."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_url_for_community(url: Optional[str]) -> Optional[str]:
    """Normalizes URL host and path for robust matching across reports."""
    if not url:
        return None
    cleaned = url.strip().lower()
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    try:
        parsed = urlparse(cleaned)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path.rstrip("/")
        return f"{host}{path}"
    except Exception:
        return url.strip().lower()


def generate_reference_code(db: Session) -> str:
    """Generates GAR-{year}-{seq:06d} reference code using Postgres sequence."""
    now = datetime.now(timezone.utc)
    try:
        seq = db.execute(text("SELECT nextval('report_ref_seq');")).scalar()
        if seq is not None:
            return f"GAR-{now.year}-{int(seq):06d}"
    except Exception:
        # Fallback in environments where sequence is not initialized
        pass

    count = db.execute(select(func.count(Report.id))).scalar() or 0
    return f"GAR-{now.year}-{(count + 1):06d}"


def create_report(
    db: Session,
    user_id: uuid.UUID,
    payload: ReportCreateRequest,
) -> Report:
    """
    Creates a new scam/fraud incident report for the authenticated user.
    Enforces honest status starting at 'submitted' with an audit history note.
    """
    ref_code = generate_reference_code(db)

    report = Report(
        id=uuid.uuid4(),
        reference_code=ref_code,
        user_id=user_id,
        scan_id=payload.scan_id,
        scam_type=payload.scam_type,
        content=payload.content,
        scammer_phone=payload.scammer_phone,
        scammer_upi=payload.scammer_upi,
        scammer_url=payload.scammer_url,
        amount_lost=payload.amount_lost,
        incident_date=payload.incident_date,
        status="submitted",
        # Backward compatibility fields
        title=f"{payload.scam_type.upper()} Scam Report",
        description=payload.content,
        category=payload.scam_type,
    )

    db.add(report)

    # Initial status history entry
    status_entry = ReportStatusHistory(
        id=uuid.uuid4(),
        report_id=report.id,
        from_status=None,
        to_status="submitted",
        note="Report submitted to GARUDA",
        changed_by=user_id,
    )
    db.add(status_entry)

    db.commit()
    db.refresh(report)
    return report


def get_user_reports(
    db: Session,
    user_id: uuid.UUID,
) -> List[Report]:
    """Retrieves all reports filed by the authenticated user, newest first."""
    stmt = (
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(Report.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_report_by_id(
    db: Session,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report:
    """
    Retrieves a single report by ID.
    Strictly enforces ownership: returns 404 for other users to prevent IDOR probing.
    """
    stmt = select(Report).where(Report.id == report_id, Report.user_id == user_id)
    report = db.execute(stmt).scalar_one_or_none()
    if not report:
        raise AppException(
            code="REPORT_NOT_FOUND",
            message="Report not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return report


def check_community_reports(
    db: Session,
    urls: Optional[List[str]] = None,
    upis: Optional[List[str]] = None,
    phones: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Community warning check:
    When a URL, UPI ID, or phone number has been reported by 2+ DIFFERENT users,
    returns the COMMUNITY_REPORTED threat indicator with medium severity, 0.4 weight,
    and label 'Reported by N GARUDA users'.
    Never reveals the identity or details of who reported.
    """
    clean_urls = [u.strip().lower() for u in (urls or []) if u and u.strip()]
    clean_upis = [u.strip().lower() for u in (upis or []) if u and u.strip()]
    clean_phones = [normalize_phone_digits(p) for p in (phones or []) if p and normalize_phone_digits(p)]

    if not clean_urls and not clean_upis and not clean_phones:
        return None

    # Find matching distinct reporters in reports table
    matching_user_ids = set()

    # 1. Check Scammer URLs
    if clean_urls:
        url_conditions = []
        for u in clean_urls:
            norm_u = normalize_url_for_community(u)
            url_conditions.append(func.lower(Report.scammer_url) == u)
            if norm_u:
                url_conditions.append(func.lower(Report.scammer_url).ilike(f"%{norm_u}%"))
        
        stmt = select(Report.user_id).where(
            Report.scammer_url.is_not(None),
            or_(*url_conditions),
        )
        for uid in db.execute(stmt).scalars():
            matching_user_ids.add(uid)

    # 2. Check Scammer UPIs
    if clean_upis:
        upi_conditions = [func.lower(Report.scammer_upi) == u for u in clean_upis]
        stmt = select(Report.user_id).where(
            Report.scammer_upi.is_not(None),
            or_(*upi_conditions),
        )
        for uid in db.execute(stmt).scalars():
            matching_user_ids.add(uid)

    # 3. Check Scammer Phones
    if clean_phones:
        phone_conditions = []
        for p in clean_phones:
            phone_conditions.append(Report.scammer_phone.ilike(f"%{p}%"))
        
        stmt = select(Report.user_id).where(
            Report.scammer_phone.is_not(None),
            or_(*phone_conditions),
        )
        for uid in db.execute(stmt).scalars():
            matching_user_ids.add(uid)

    distinct_count = len(matching_user_ids)
    if distinct_count >= 2:
        return {
            "code": "COMMUNITY_REPORTED",
            "label": f"Reported by {distinct_count} GARUDA users",
            "severity": "medium",
            "weight": 0.4,
            "evidence": f"Flagged by {distinct_count} community incident reports",
        }

    return None
