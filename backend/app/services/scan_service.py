import base64
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from fastapi import status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.errors import AppException
from app.engine import engine
from app.models.scan import (
    AnalysisResult,
    Image,
    Message,
    QRCode,
    Scan,
    ThreatIndicator,
    URL,
)
from app.schemas.scan import (
    CategoryInfo,
    RiskInfo,
    ScanListItem,
)

# Standard category labels from detection engine specification
CATEGORY_LABELS: Dict[str, str] = {
    "digital_arrest_scam": "Law Enforcement / Digital Arrest Scam",
    "family_emergency_scam": "Family Emergency Impersonation Scam",
    "upi_pin_fraud": "UPI PIN / Collect Request Scam",
    "qr_reward_scam": "Potential QR / Reward Scam",
    "investment_fraud": "Unregulated Investment / Stock Tips Scheme",
    "fake_job_fraud": "Part-Time Job / Task Fraud",
    "loan_advance_fee": "Instant Loan / Advance Fee Scam",
    "lottery_scam": "Lottery / Lucky Draw Fee Fraud",
    "tax_refund_phishing": "Tax Refund Phishing Scam",
    "kyc_suspension_phishing": "KYC / Account Suspension Threat",
    "otp_theft": "OTP Solicitation / Account Takeover",
    "phishing_link": "Deceptive / Phishing Website",
    "unverified_link": "Unverified Link Destination",
    "unverifiable": "Unverifiable Content",
    "legitimate_communication": "Likely Legitimate Communication",
    "suspicious_communication": "Suspicious Communication",
}

# Standard risk band labels
RISK_LABELS: Dict[str, str] = {
    "likely_safe": "Likely Safe",
    "suspicious": "Suspicious",
    "medium": "Medium Risk",
    "high": "High Risk",
    "critical": "Critical Threat",
    "unable_to_verify": "Unable to Verify",
}


def encode_cursor(created_at: datetime, scan_id: uuid.UUID) -> str:
    """Encodes created_at and scan_id into an opaque URL-safe base64 string for pagination."""
    raw = f"{created_at.isoformat()}|{str(scan_id)}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> Tuple[datetime, uuid.UUID]:
    """Decodes an opaque pagination cursor into (created_at, scan_id)."""
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        dt_str, id_str = raw.split("|", 1)
        return datetime.fromisoformat(dt_str), uuid.UUID(id_str)
    except Exception:
        raise AppException(
            code="INVALID_CURSOR",
            message="Invalid pagination cursor format.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# ==============================================================================
# REUSABILITY NOTE FOR FUTURE ANALYZERS (URL, QR, Image):
# The `save_scan_record` function below serves as the single unified persistence
# pipeline across all scan types.
#
# - URL analyzer (Chunk 6):
#     save_scan_record(
#         db=db,
#         user_id=user_id,
#         scan_id=scan_id,
#         scan_type="url",
#         input_sha256=hashlib.sha256(raw_url.encode()).hexdigest(),
#         analysis_dict=url_analysis,
#         urls_data=[{"raw": raw_url, "normalized": norm_url, "domain": reg_domain, "source": "direct"}],
#     )
#
# - QR analyzer (Chunk 7):
#     save_scan_record(
#         db=db,
#         user_id=user_id,
#         scan_id=scan_id,
#         scan_type="qr",
#         input_sha256=payload_sha256,
#         analysis_dict=qr_analysis,
#         qr_data={"payload": payload, "payload_type": ptype, "upi_payee": payee, "upi_name": name, "upi_amount": amount},
#         urls_data=extracted_urls,
#     )
# ==============================================================================
def save_scan_record(
    db: Session,
    user_id: uuid.UUID,
    scan_id: uuid.UUID,
    scan_type: str,
    input_sha256: Optional[str],
    analysis_dict: Dict[str, Any],
    message_content: Optional[str] = None,
    detected_language: Optional[str] = None,
    urls_data: Optional[List[Dict[str, Any]]] = None,
    qr_data: Optional[Dict[str, Any]] = None,
    image_data: Optional[Dict[str, Any]] = None,
    persisted_content: bool = True,
) -> Scan:
    """
    Persists scan, associated input entities, analysis results (including legitimacy signals),
    threat indicators, and detected URLs in a single atomic database transaction.
    """
    # 1. Scans record
    scan = Scan(
        id=scan_id,
        user_id=user_id,
        scan_type=scan_type,
        status="done",
        input_sha256=input_sha256,
        persisted_content=persisted_content,
    )
    db.add(scan)

    # 2. Message record (for message scans)
    if message_content is not None:
        msg = Message(
            id=uuid.uuid4(),
            scan_id=scan_id,
            content=message_content,
            detected_language=detected_language,
        )
        db.add(msg)

    # 3. QR code record (for QR scans)
    if qr_data is not None:
        qr = QRCode(
            id=uuid.uuid4(),
            scan_id=scan_id,
            payload=qr_data.get("payload", ""),
            payload_type=qr_data.get("payload_type", "other"),
            upi_payee=qr_data.get("upi_payee"),
            upi_name=qr_data.get("upi_name"),
            upi_amount=qr_data.get("upi_amount"),
        )
        db.add(qr)

    # 4. AnalysisResult record (including legitimacy signals and recommendations)
    cat_val = analysis_dict.get("category", {})
    category_code = cat_val.get("code") if isinstance(cat_val, dict) else str(cat_val)
    risk_val = analysis_dict.get("risk", {})

    analysis_id = uuid.uuid4()
    analysis_result = AnalysisResult(
        id=analysis_id,
        scan_id=scan_id,
        risk_score=risk_val.get("score", 0),
        risk_level=risk_val.get("level", "likely_safe"),
        confidence=float(analysis_dict.get("confidence", 0.0)),
        verification_status=analysis_dict.get("verification_status", "unverified"),
        category=category_code,
        summary=analysis_dict.get("summary", ""),
        legitimacy_signals=analysis_dict.get("legitimacy_signals", []),
        recommendations=analysis_dict.get("recommendations", []),
        verify_steps=analysis_dict.get("verify_steps", []),
        intel_status=analysis_dict.get("intel", []),
        engine_version=analysis_dict.get("engine_version", "2.0.0"),
    )
    db.add(analysis_result)

    # 5. Threat Indicators
    for ind in analysis_dict.get("indicators", []):
        indicator_row = ThreatIndicator(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            code=ind.get("code", "UNKNOWN"),
            label=ind.get("label", ""),
            severity=ind.get("severity", "low"),
            weight=float(ind.get("weight", 0.0)),
            evidence=ind.get("evidence"),
        )
        db.add(indicator_row)

    # 6. Extracted URLs (source=message for message scans)
    for u in (urls_data or []):
        raw_u = u.get("raw") or u.get("raw_url") or ""
        norm_u = u.get("normalized") or u.get("normalized_url") or raw_u
        dom = u.get("domain") or u.get("registered_domain") or ""
        src = u.get("source") or ("message" if scan_type == "message" else scan_type)

        url_row = URL(
            id=uuid.uuid4(),
            scan_id=scan_id,
            raw_url=raw_u,
            normalized_url=norm_u,
            registered_domain=dom[:255] if dom else "unknown",
            source=src,
        )
        db.add(url_row)

    # Single transaction commit
    db.commit()
    db.refresh(scan)
    return scan


def analyze_message(
    db: Session,
    user_id: uuid.UUID,
    text: str,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Analyzes message text via detection engine (no duplicate logic) and conditionally
    persists scan and related entities if save=True in one transaction. If save=False, stores nothing.
    """
    input_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    scan_id = uuid.uuid4()

    # Call pure Python engine.analyze (single source of truth)
    result = engine.analyze(raw_text=text, scan_id=str(scan_id) if save else None)

    if save:
        save_scan_record(
            db=db,
            user_id=user_id,
            scan_id=scan_id,
            scan_type="message",
            input_sha256=input_sha,
            analysis_dict=result,
            message_content=text,
            detected_language=result.get("extracted", {}).get("language"),
            urls_data=result.get("extracted", {}).get("urls", []),
            persisted_content=True,
        )
        result["scan_id"] = str(scan_id)
    else:
        result["scan_id"] = None

    return result


def get_user_scans(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 20,
    cursor: Optional[str] = None,
    scan_type: Optional[str] = None,
    risk_level: Optional[str] = None,
) -> Tuple[List[ScanListItem], Optional[str], bool]:
    """
    Retrieves user's own scans with cursor pagination (?limit=&cursor=), newest first.
    Filters by scan_type and risk_level.
    """
    limit = max(1, min(limit, 100))

    query = (
        select(Scan)
        .where(Scan.user_id == user_id)
        .options(
            joinedload(Scan.analysis_result),
            joinedload(Scan.message),
        )
    )

    if scan_type:
        query = query.where(Scan.scan_type == scan_type)

    if risk_level:
        query = query.join(Scan.analysis_result).where(AnalysisResult.risk_level == risk_level)

    if cursor:
        c_dt, c_id = decode_cursor(cursor)
        query = query.where(
            or_(
                Scan.created_at < c_dt,
                and_(Scan.created_at == c_dt, Scan.id < c_id),
            )
        )

    query = query.order_by(Scan.created_at.desc(), Scan.id.desc()).limit(limit + 1)
    results = db.execute(query).scalars().all()

    has_more = len(results) > limit
    page_items = results[:limit]

    next_cursor = None
    if has_more and page_items:
        last_item = page_items[-1]
        next_cursor = encode_cursor(last_item.created_at, last_item.id)

    items: List[ScanListItem] = []
    for s in page_items:
        res = s.analysis_result
        if not res:
            continue
        cat_label = CATEGORY_LABELS.get(res.category, res.category.replace("_", " ").title())
        risk_label = RISK_LABELS.get(res.risk_level, res.risk_level.replace("_", " ").title())
        preview = s.message.content[:120] if s.message else None

        items.append(
            ScanListItem(
                id=s.id,
                scan_type=s.scan_type,
                status=s.status,
                created_at=s.created_at,
                risk=RiskInfo(score=res.risk_score, level=res.risk_level, label=risk_label),
                category=CategoryInfo(code=res.category, label=cat_label),
                confidence=res.confidence,
                verification_status=res.verification_status,
                summary=res.summary,
                content_preview=preview,
            )
        )

    return items, next_cursor, has_more


def get_scan_by_id(db: Session, user_id: uuid.UUID, scan_id: uuid.UUID) -> Dict[str, Any]:
    """
    Returns full saved analysis for scan_id.
    Returns 404 if scan is missing OR belongs to another user (prevents IDOR).
    """
    scan = db.execute(
        select(Scan)
        .where(Scan.id == scan_id)
        .options(
            selectinload(Scan.analysis_result).selectinload(AnalysisResult.threat_indicators),
            selectinload(Scan.message),
            selectinload(Scan.urls),
            selectinload(Scan.qr_codes),
        )
    ).scalar_one_or_none()

    if not scan or scan.user_id != user_id:
        raise AppException(
            code="NOT_FOUND",
            message="Scan not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    res = scan.analysis_result
    if not res:
        raise AppException(
            code="NOT_FOUND",
            message="Scan analysis not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    cat_label = CATEGORY_LABELS.get(res.category, res.category.replace("_", " ").title())
    risk_label = RISK_LABELS.get(res.risk_level, res.risk_level.replace("_", " ").title())

    indicators = [
        {
            "code": ind.code,
            "label": ind.label,
            "severity": ind.severity,
            "weight": ind.weight,
            "evidence": ind.evidence,
        }
        for ind in res.threat_indicators
    ]

    extracted_urls = [
        {
            "raw": u.raw_url,
            "normalized": u.normalized_url,
            "domain": u.registered_domain,
            "source": u.source,
        }
        for u in scan.urls
    ]

    qr_detail = None
    if scan.qr_codes:
        qr_obj = scan.qr_codes[0]
        qr_detail = {
            "payload": qr_obj.payload,
            "payload_type": qr_obj.payload_type,
            "upi_payee": qr_obj.upi_payee,
            "upi_name": qr_obj.upi_name,
            "upi_amount": float(qr_obj.upi_amount) if qr_obj.upi_amount is not None else None,
        }

    return {
        "scan_id": str(scan.id),
        "scan_type": scan.scan_type,
        "risk": {
            "score": res.risk_score,
            "level": res.risk_level,
            "label": risk_label,
        },
        "confidence": res.confidence,
        "verification_status": res.verification_status,
        "category": {
            "code": res.category,
            "label": cat_label,
        },
        "summary": res.summary,
        "indicators": indicators,
        "legitimacy_signals": res.legitimacy_signals,
        "recommendations": res.recommendations,
        "verify_steps": res.verify_steps,
        "extracted": {
            "urls": extracted_urls,
            "qr": qr_detail,
            "upi": None,
            "phone": [],
            "language": scan.message.detected_language if scan.message else None,
        },
        "intel": res.intel_status,
        "engine_version": res.engine_version,
        "created_at": scan.created_at,
        "message": {
            "content": scan.message.content,
            "detected_language": scan.message.detected_language,
        }
        if scan.message
        else None,
    }


def delete_scan_by_id(db: Session, user_id: uuid.UUID, scan_id: uuid.UUID) -> None:
    """
    Deletes the user's own scan and all linked records via database cascade.
    Returns 404 if scan belongs to another user (prevents IDOR).
    """
    scan = db.execute(
        select(Scan).where(Scan.id == scan_id)
    ).scalar_one_or_none()

    if not scan or scan.user_id != user_id:
        raise AppException(
            code="NOT_FOUND",
            message="Scan not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    db.delete(scan)
    db.commit()
