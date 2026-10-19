"""
GARUDA QR Analyzer
==================
Analyzes QR code payloads and decodes QR images in-memory without ever opening
destinations or writing images to disk.

Dispatches payload content:
  1. Starts with upi:// -> Static UPI Analyzer (analyze_upi)
  2. Web link (http/https or domain) -> Static URL Analyzer (analyze_url)
  3. Plain text -> Plain Text QR (likely_safe; suspicious if phone + prize/urgency)
  4. Empty -> unable_to_verify
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote_plus

import cv2
import numpy as np

from app.engine.analyzers.upi_analyzer import (
    ALWAYS_RECOMMENDATION,
    Indicator,
    analyze_upi,
    band,
    noisy_or,
)
from app.engine.analyzers.url_analyzer import analyze_url
from app.engine.extractors.upi import claims_brand_or_authority

ENGINE_VERSION = "qr-1.0.0"

# Maximum upload limit: 5 MB
MAX_QR_SIZE_BYTES = 5 * 1024 * 1024

# Magic byte signatures for accepted image formats
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPG_MAGIC = b"\xff\xd8\xff"
RIFF_MAGIC = b"RIFF"
WEBP_MAGIC = b"WEBP"

QR_VERIFY_STEPS = [
    "Verify the destination details with the recipient or physical vendor before proceeding.",
    "Inspect physical QR stickers to ensure they have not been placed over genuine merchant codes.",
    "Remember: Scanning a QR code can only SEND money, never receive it.",
]

URL_CATEGORY_CODES = {
    "phishing": "phishing_link",
    "gambling": "illegal_betting",
    "adult": "restricted_adult",
    "suspicious_link": "suspicious_link",
    "none": "no_warning_signs",
}

PRIZE_WORDS = {
    "prize", "prizes", "reward", "rewards", "cashback", "cash back",
    "won", "winner", "winning", "lottery", "bonus", "claim", "claimed",
    "gift", "inam", "inaam", "puraskar", "dabbulu", "crore", "lakh", "congratulations",
}

URGENT_WORDS = {
    "urgent", "urgently", "immediately", "blocked", "suspended", "arrest",
    "police", "court", "verify now", "kyc", "expire", "expires",
    "disconnection", "bijli", "fine", "penalty", "action required",
}


@dataclass
class QrResult:
    input: str
    valid: bool
    qr_type: str = "text"              # upi | url | text | wifi
    score: int = 0
    level: str = "unable_to_verify"
    label: str = "Unable to Verify"
    category: str = "none"
    category_label: str = ""
    summary: str = ""
    indicators: list[Any] = field(default_factory=list)
    legitimacy_signals: list[Any] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    verify_steps: list[str] = field(default_factory=list)
    verification_status: str = "unverified"
    error: str | None = None
    upi_data: dict[str, Any] | None = None
    url_data: dict[str, Any] | None = None
    engine_version: str = ENGINE_VERSION

    def __getitem__(self, item: str) -> Any:
        if item == "risk":
            return {"score": self.score, "level": self.level, "label": self.label}
        if item == "category":
            return {"code": self.category, "label": self.category_label}
        if item == "extracted":
            return {
                "qr": {"content": self.input, "type": self.qr_type},
                "upi": self.upi_data,
                "urls": [self.url_data] if self.url_data else [],
            }
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "valid": self.valid,
            "qr_type": self.qr_type,
            "score": self.score,
            "level": self.level,
            "label": self.label,
            "category": self.category,
            "category_label": self.category_label,
            "summary": self.summary,
            "indicators": [i.__dict__ if hasattr(i, "__dict__") else i for i in self.indicators],
            "legitimacy_signals": [i.__dict__ if hasattr(i, "__dict__") else i for i in self.legitimacy_signals],
            "recommendations": self.recommendations,
            "verify_steps": self.verify_steps,
            "verification_status": self.verification_status,
            "error": self.error,
            "upi_data": self.upi_data,
            "url_data": self.url_data,
            "engine_version": self.engine_version,
        }

    def to_analysis_response(self) -> dict[str, Any]:
        """Formats the result into the standard AnalysisResponse dictionary."""
        indicators_list = [i.__dict__ if hasattr(i, "__dict__") else i for i in self.indicators]
        signals_list = [i.__dict__ if hasattr(i, "__dict__") else i for i in self.legitimacy_signals]

        has_blocklist = any(i.get("code", "").startswith("BLOCKLIST") for i in indicators_list)
        has_official_allowlist = (
            self.qr_type == "url"
            and any(s.get("code", "").startswith("ALLOWLIST") for s in signals_list)
        )

        if has_blocklist or has_official_allowlist:
            confidence = 0.90
        elif indicators_list:
            confidence = 0.75
        else:
            # When there are no indicators (only legitimacy signals like a common PSP handle),
            # confidence must be 0.5, not 0.9. A normal UPI ID does not prove the payee is genuine.
            confidence = 0.50

        verification_status = self.verification_status
        if not indicators_list and (self.qr_type == "upi" or verification_status in ("standard_psp_handle", "unverified", "")):
            verification_status = "no_warning_signs_found"

        return {
            "scan_type": "qr",
            "risk": {
                "score": self.score,
                "level": self.level,
                "label": self.label,
            },
            "confidence": confidence,
            "verification_status": verification_status,
            "category": {
                "code": self.category,
                "label": self.category_label,
            },
            "summary": self.summary,
            "indicators": indicators_list,
            "legitimacy_signals": signals_list,
            "recommendations": self.recommendations,
            "verify_steps": self.verify_steps or QR_VERIFY_STEPS,
            "extracted": {
                "qr": {"content": self.input, "type": self.qr_type},
                "upi": self.upi_data,
                "urls": [self.url_data] if self.url_data else [],
                "phone": [],
                "language": None,
            },
            "intel": [
                {
                    "source": "garuda_lists",
                    "status": "matched" if verification_status not in ("unverified", "no_warning_signs_found") else "not_found",
                }
            ],
            "engine_version": self.engine_version,
        }


# ---------------------------------------------------------------------------
# 1. Image Decoding (In-memory, never saved)
# ---------------------------------------------------------------------------

def validate_qr_image(file_bytes: bytes) -> dict[str, Any]:
    """
    Validates image bytes in memory:
    - Size <= 5 MB
    - PNG, JPG, or WEBP magic bytes
    """
    if not file_bytes:
        raise ValueError("Image payload is empty.")

    size = len(file_bytes)
    if size > MAX_QR_SIZE_BYTES:
        raise ValueError(
            f"Image size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of 5 MB."
        )

    if file_bytes.startswith(PNG_MAGIC):
        mime_type = "image/png"
    elif file_bytes.startswith(JPG_MAGIC):
        mime_type = "image/jpeg"
    elif file_bytes.startswith(RIFF_MAGIC) and len(file_bytes) >= 12 and file_bytes[8:12] == WEBP_MAGIC:
        mime_type = "image/webp"
    else:
        raise ValueError(
            "Invalid image format. Only PNG, JPG, and WEBP formats are accepted based on magic-byte verification."
        )

    return {"valid": True, "mime_type": mime_type, "size_bytes": size}


def decode_qr_image(file_bytes: bytes) -> str | None:
    """
    Decodes QR code from in-memory image bytes using OpenCV (cv2.QRCodeDetector).
    Rejects files over 5 MB or non-images. Never saves the image anywhere.
    """
    validate_qr_image(file_bytes)

    np_arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image data into valid image matrix.")

    detector = cv2.QRCodeDetector()

    # Pass 1: Direct color image detection
    payload, _points, _ = detector.detectAndDecode(img)
    if payload and payload.strip():
        return payload.strip()

    # Pass 2: Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    payload, _points, _ = detector.detectAndDecode(gray)
    if payload and payload.strip():
        return payload.strip()

    # Pass 3: Otsu thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    payload, _points, _ = detector.detectAndDecode(thresh)
    if payload and payload.strip():
        return payload.strip()

    # Pass 4: Border padding (helps when QR extends to image edges)
    padded = cv2.copyMakeBorder(gray, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    payload, _points, _ = detector.detectAndDecode(padded)
    if payload and payload.strip():
        return payload.strip()

    # Pass 5: pyzbar fallback if available
    try:
        from pyzbar import pyzbar
        results = pyzbar.decode(img) or pyzbar.decode(gray)
        if results:
            decoded_val = results[0].data.decode("utf-8", errors="replace").strip()
            if decoded_val:
                return decoded_val
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# 2. Content Analysis
# ---------------------------------------------------------------------------

def _is_web_link(text: str) -> bool:
    """Checks if text looks like a web link (http/https or a domain)."""
    cleaned = text.strip().lower()
    if cleaned.startswith(("http://", "https://")):
        return True
    # Domain pattern: letters/digits, dot, valid TLD of at least 2 letters
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?$",
        re.IGNORECASE,
    )
    return bool(domain_pattern.match(cleaned))


def _analyze_qr_content_base(content: str) -> QrResult:
    """
    Analyzes QR payload content:
    - starts with upi:// -> analyze_upi
    - looks like a web link (http/https or domain) -> analyze_url
    - plain text -> likely_safe 'Plain Text QR' (suspicious if phone + prize/urgent words)
    - empty -> unable_to_verify
    """
    raw = (content or "").strip()
    if not raw:
        return QrResult(
            input=content or "",
            valid=False,
            score=0,
            level="unable_to_verify",
            label="Unable to Verify",
            category="unverifiable",
            category_label="Unverifiable Content",
            summary="QR payload is empty or unreadable.",
            recommendations=[ALWAYS_RECOMMENDATION],
            verify_steps=QR_VERIFY_STEPS,
            error="QR content cannot be empty.",
        )

    unquoted = unquote_plus(raw)

    # 1. UPI Payment Link
    if raw.lower().startswith("upi://") or unquoted.lower().startswith("upi://"):
        u_res = analyze_upi(raw)
        if not u_res.valid:
            return QrResult(
                input=raw,
                valid=False,
                qr_type="upi",
                score=0,
                level="unable_to_verify",
                label="Unable to Verify",
                category="unverifiable",
                category_label="Unverifiable Content",
                summary=u_res.summary or "Invalid UPI payment link.",
                error=u_res.error or "Invalid UPI address.",
                recommendations=u_res.recommendations or [ALWAYS_RECOMMENDATION],
                verify_steps=QR_VERIFY_STEPS,
                upi_data={"pa": u_res.pa, "pn": u_res.pn, "am": u_res.am, "tn": u_res.tn},
            )

        indicators = list(u_res.indicators)

        # Check if authority / brand is claimed that wasn't already caught (e.g. tsspdcl, bescom, electricity dept)
        claimed = claims_brand_or_authority(u_res.pn or "") or claims_brand_or_authority(u_res.username or "")
        if claimed and not any(i.code.startswith("UPI_BRAND") for i in indicators):
            indicators.append(
                Indicator(
                    code="UPI_BRAND_IMPERSONATION",
                    label=f"Payee name or handle claims official entity or utility ('{claimed.upper()}')",
                    severity="high",
                    weight=0.65,
                    evidence=f"Payee: '{u_res.pn}', VPA: '{u_res.pa}'",
                )
            )

        # Check for coercive threat in transaction note (disconnection, power cut, pin entry)
        tn_lower = (u_res.tn or "").lower()
        if tn_lower and not any(i.code == "UPI_BAIT_NOTE" for i in indicators):
            threat_match = re.search(r"\b(?:disconnection|disconnect|power off|avoid disconnection|enter\s+(?:upi\s+)?pin)\b", tn_lower)
            if threat_match:
                indicators.append(
                    Indicator(
                        code="UPI_BAIT_NOTE",
                        label="Transaction note contains coercive disconnection threat or PIN solicitation",
                        severity="high",
                        weight=0.55,
                        evidence=f"tn='{u_res.tn}'",
                    )
                )

        score = round(100 * noisy_or([i.weight for i in indicators]))
        level, label = band(score)

        cat_code = "upi_fraud" if level == "high" else (
            "suspicious_upi" if level in ("medium", "suspicious") else "no_warning_signs"
        )
        cat_label = {
            "upi_fraud": "UPI Payment Fraud",
            "suspicious_upi": "Suspicious UPI Payment",
            "no_warning_signs": "Likely Legitimate UPI",
        }.get(cat_code, u_res.category_label or "UPI Payment")

        recs = list(u_res.recommendations)
        if ALWAYS_RECOMMENDATION not in recs:
            recs.insert(0, ALWAYS_RECOMMENDATION)

        summary = u_res.summary
        if indicators and not u_res.indicators:
            reasons = "; ".join(i.label.lower() for i in indicators[:3])
            summary = f"This UPI link shows warning signs: {reasons}."

        legit_signals = list(u_res.legitimacy_signals) if not indicators else []

        return QrResult(
            input=raw,
            valid=True,
            qr_type="upi",
            score=score,
            level=level,
            label=label,
            category=cat_code,
            category_label=cat_label,
            summary=summary,
            indicators=indicators,
            legitimacy_signals=legit_signals,
            recommendations=recs,
            verify_steps=QR_VERIFY_STEPS,
            verification_status="unverified" if indicators else "no_warning_signs_found",
            upi_data={"pa": u_res.pa, "pn": u_res.pn, "am": u_res.am, "tn": u_res.tn},
        )

    # 2. Web Link (URL)
    if _is_web_link(raw):
        url_res = analyze_url(raw)
        if not url_res.valid:
            return QrResult(
                input=raw,
                valid=False,
                qr_type="url",
                score=0,
                level="unable_to_verify",
                label="Unable to Verify",
                category="unverifiable",
                category_label="Unverifiable Content",
                summary=url_res.summary or "Invalid web address.",
                error=url_res.error or "Invalid web address.",
                recommendations=[ALWAYS_RECOMMENDATION],
                verify_steps=QR_VERIFY_STEPS,
            )

        cat_code = URL_CATEGORY_CODES.get(url_res.category, url_res.category)
        recs = list(url_res.recommendations)
        if ALWAYS_RECOMMENDATION not in recs:
            recs.insert(0, ALWAYS_RECOMMENDATION)

        return QrResult(
            input=raw,
            valid=True,
            qr_type="url",
            score=url_res.score,
            level=url_res.level,
            label=url_res.label,
            category=cat_code,
            category_label=url_res.category_label,
            summary=url_res.summary,
            indicators=url_res.indicators,
            legitimacy_signals=url_res.legitimacy_signals,
            recommendations=recs,
            verify_steps=QR_VERIFY_STEPS,
            verification_status=url_res.verification_status,
            url_data={
                "raw": url_res.input,
                "normalized": url_res.normalized_url,
                "domain": url_res.registered_domain,
                "source": "qr",
            },
        )

    # 3. Wi-Fi Configuration
    if raw.upper().startswith("WIFI:"):
        return QrResult(
            input=raw,
            valid=True,
            qr_type="wifi",
            score=0,
            level="likely_safe",
            label="Likely Safe",
            category="plain_text_qr",
            category_label="Plain Text QR",
            summary="This QR code contains local Wi-Fi wireless network configuration credentials.",
            indicators=[],
            legitimacy_signals=[
                Indicator(
                    code="LEGIT_WIFI_CONFIG",
                    label="Standard Wi-Fi network configuration QR format",
                    severity="low",
                    weight=0.0,
                    evidence=raw[:40],
                )
            ],
            recommendations=[
                ALWAYS_RECOMMENDATION,
                "Only connect to Wi-Fi networks belonging to trusted venues or providers.",
            ],
            verify_steps=QR_VERIFY_STEPS,
            verification_status="wifi_config",
        )

    # 4. Plain Text
    words = set(re.findall(r"[a-zA-Z]+", raw.lower()))
    phone_match = re.search(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b|\b\d{10}\b", raw)
    has_bait = bool(words & PRIZE_WORDS or words & URGENT_WORDS)

    if phone_match and has_bait:
        matched_bait_terms = list(words & (PRIZE_WORDS | URGENT_WORDS))
        return QrResult(
            input=raw,
            valid=True,
            qr_type="text",
            score=35,
            level="suspicious",
            label="Suspicious",
            category="suspicious_upi",
            category_label="Suspicious Plain Text QR",
            summary=(
                "This QR code contains plain text with a phone number and urgency or prize wording. "
                "Scammers often encode plain text contact numbers to bypass URL scanners."
            ),
            indicators=[
                Indicator(
                    code="QR_TEXT_SUSPICIOUS",
                    label="Plain text QR contains phone number with urgency or prize solicitation",
                    severity="medium",
                    weight=0.35,
                    evidence=f"Phone: {phone_match.group(0)}, Wording: {', '.join(matched_bait_terms[:2])}",
                )
            ],
            legitimacy_signals=[],
            recommendations=[
                ALWAYS_RECOMMENDATION,
                "Do not call unknown phone numbers found in QR codes.",
                "Never share OTP, passwords, or UPI PIN over phone calls.",
            ],
            verify_steps=QR_VERIFY_STEPS,
            verification_status="unverified",
        )

    return QrResult(
        input=raw,
        valid=True,
        qr_type="text",
        score=0,
        level="likely_safe",
        label="Likely Safe",
        category="plain_text_qr",
        category_label="Plain Text QR",
        summary="This QR code contains plain text with no deceptive links, payment traps, or phishing indicators.",
        indicators=[],
        legitimacy_signals=[
            Indicator(
                code="LEGIT_PLAIN_TEXT",
                label="Benign plain text payload without URLs or payment instructions",
                severity="low",
                weight=0.0,
                evidence=raw[:60],
            )
        ],
        recommendations=[
            ALWAYS_RECOMMENDATION,
            "Always verify text details before acting on instructions.",
        ],
        verify_steps=QR_VERIFY_STEPS,
        verification_status="plain_text",
    )



def _apply_context(res: QrResult, context: str | None = None) -> QrResult:
    """
    Augments QR analysis result with user-reported scanning context.
    - receive_money: QR codes can only SEND money, claiming to receive is a scam.
    - stranger_request: Paying on instruction of a caller/stranger adds moderate risk.
    - known_payee / null: no change.
    """
    if not res.valid or not context or context in ("known_payee", "none", "null", ""):
        return res

    context_indicator: Indicator | None = None
    if context == "receive_money":
        context_indicator = Indicator(
            code="QR_RECEIVE_MONEY_CLAIM",
            label="You were told scanning will give you money - QR codes can only SEND money",
            severity="high",
            weight=0.85,
            evidence="User indicated they were told scanning will receive money, refund, or prize",
        )
    elif context == "stranger_request":
        context_indicator = Indicator(
            code="QR_STRANGER_REQUEST",
            label="A stranger or caller asked you to scan and pay",
            severity="medium",
            weight=0.4,
            evidence="User indicated a stranger or caller asked them to scan and pay",
        )

    if context_indicator is None:
        return res

    if not any(i.code == context_indicator.code for i in res.indicators):
        res.indicators.append(context_indicator)

    # When indicators exist, clear benign legitimacy signals
    res.legitimacy_signals = []

    res.score = round(100 * noisy_or([i.weight for i in res.indicators]))
    res.level, res.label = band(res.score)

    if res.qr_type == "upi":
        cat_code = "upi_fraud" if res.level == "high" else (
            "suspicious_upi" if res.level in ("medium", "suspicious") else "no_warning_signs"
        )
        res.category = cat_code
        res.category_label = {
            "upi_fraud": "UPI Payment Fraud",
            "suspicious_upi": "Suspicious UPI Payment",
            "no_warning_signs": "Likely Legitimate UPI",
        }.get(cat_code, "UPI Payment")
    elif res.qr_type in ("text", "wifi"):
        if res.level == "high":
            res.category = "qr_scam"
            res.category_label = "QR Payment Scam"
        elif res.level in ("medium", "suspicious"):
            res.category = "suspicious_qr"
            res.category_label = "Suspicious QR Code"
    elif res.qr_type == "url":
        if res.level == "high" and res.category in ("none", "no_warning_signs"):
            res.category = "qr_scam"
            res.category_label = "QR Phishing / Fraud"

    recs = list(res.recommendations)
    if ALWAYS_RECOMMENDATION not in recs:
        recs.insert(0, ALWAYS_RECOMMENDATION)
    if res.level == "high":
        for hr in [
            "Do NOT approve this payment or enter your UPI PIN.",
            "Entering your UPI PIN will DEBIT money from your bank account, not credit it.",
            "If you were told you will receive money by scanning this QR code, this is 100% a scam.",
            "Report fraudulent QR codes at cybercrime.gov.in or call helpline 1930.",
        ]:
            if hr not in recs:
                recs.append(hr)
    elif res.level in ("medium", "suspicious"):
        for mr in [
            "Verify the recipient's identity independently before sending funds.",
            "Never enter your UPI PIN unless you intend to send money.",
        ]:
            if mr not in recs:
                recs.append(mr)
    res.recommendations = recs

    reasons = "; ".join(i.label.lower() for i in res.indicators[:3])
    res.summary = f"This QR code shows warning signs: {reasons}."
    res.verification_status = "unverified"

    return res


def analyze_qr_content(content: str, context: str | None = None) -> QrResult:
    """
    Analyzes QR payload content:
    - starts with upi:// -> analyze_upi
    - looks like a web link (http/https or domain) -> analyze_url
    - plain text -> likely_safe 'Plain Text QR' (suspicious if phone + prize/urgent words)
    - empty -> unable_to_verify
    Augmented with optional scan context.
    """
    res = _analyze_qr_content_base(content)
    return _apply_context(res, context)


# ---------------------------------------------------------------------------
# 3. Compatibility Wrappers (for test_qr.py)
# ---------------------------------------------------------------------------

def analyze_qr_payload(payload: str, context: str | None = None) -> dict[str, Any]:
    """Evaluates payload and returns standard analysis response dict."""
    res = analyze_qr_content(payload, context=context)
    return res.to_analysis_response()


def analyze_qr_image(img_bytes: bytes, context: str | None = None) -> dict[str, Any]:
    """Decodes in-memory image bytes and analyzes resulting QR payload."""
    decoded = decode_qr_image(img_bytes)
    if not decoded:
        return {
            "scan_type": "qr",
            "payload": "",
            "risk": {"score": 0, "level": "unable_to_verify", "label": "Unable to Verify"},
            "confidence": 0.50,
            "verification_status": "unable_to_verify",
            "category": {"code": "unverifiable", "label": "Unverifiable Content"},
            "summary": "QR payload is empty or unreadable.",
            "indicators": [],
            "legitimacy_signals": [],
            "recommendations": [ALWAYS_RECOMMENDATION],
            "verify_steps": QR_VERIFY_STEPS,
            "extracted": {"qr": None, "upi": None, "urls": []},
            "intel": [{"source": "garuda_lists", "status": "not_found"}],
            "engine_version": ENGINE_VERSION,
        }
    return analyze_qr_payload(decoded, context=context)
