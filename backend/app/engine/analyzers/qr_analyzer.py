import re
from typing import Any
from urllib.parse import urlparse

from app.engine.analyzers.legitimacy import LegitimacySignal
from app.engine.analyzers.text_rules import Indicator
from app.engine.extractors.qr import (
    classify_payload,
    decode_qr_image,
    validate_qr_image,
)
from app.engine.extractors.upi import (
    claims_brand_or_authority,
    is_personal_handle,
    parse_upi_uri,
)
from app.engine.scoring import calculate_score

# Common reward, cashback, and refund keywords used in QR collect scams
REWARD_REFUND_KEYWORDS = [
    "reward", "cashback", "cash back", "refund", "prize", "won", "winner",
    "lottery", "lucky draw", "claim", "bonus", "gift", "voucher", "free money",
    "inam", "cashprize", "credited", "bhediye", "paise", "rupees", "₹"
]

# Patterns explicitly instructing the victim to scan or enter PIN to receive funds
# In UPI architecture, receiving money NEVER requires scanning or PIN
SCAN_TO_RECEIVE_PATTERNS = [
    r"\bscan\s+(?:to\s+)?(?:receive|get|claim|accept)\b",
    r"\breceive\s+(?:money|cashback|reward|amount|funds)\b",
    r"\benter\s+(?:upi\s+)?pin\s+to\s+receive\b",
    r"\bpin\s+(?:enter\s+)?karke\s+paise\s+lo\b",
    r"\bclaim\s+(?:your\s+)?(?:reward|cashback|refund)\b",
]

# High urgency phrasing in transaction notes
URGENT_NOTE_PATTERNS = [
    r"\b(?:immediately|urgent|urgently|today|now)\b",
    r"\b(?:within\s+\d+\s+(?:hour|hr|min|minute)s?)\b",
    r"\b(?:account|power|electricity)\s+(?:will\s+be\s+)?(?:blocked|disconnected|suspended)\b",
    r"\b(?:penalty|fine|arrest|police|cbi)\b",
]


def _detect_scan_to_receive(text: str) -> str | None:
    lowered = text.lower()
    for pat in SCAN_TO_RECEIVE_PATTERNS:
        match = re.search(pat, lowered)
        if match:
            return match.group(0)
    return None


def _detect_urgent_note(text: str) -> str | None:
    lowered = text.lower()
    for pat in URGENT_NOTE_PATTERNS:
        match = re.search(pat, lowered)
        if match:
            return match.group(0)
    return None


def _contains_reward_claim(text: str) -> str | None:
    lowered = text.lower()
    for kw in REWARD_REFUND_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def analyze_url_payload(url_str: str) -> dict[str, Any]:
    """
    Analyzes URL payload extracted from QR code without network fetching.
    ARCHITECTURE 8.8: Never open the decoded destination. Static analysis only.
    """
    # // PENDING url_analyzer: Check if Friend 2's URL analyzer is available
    try:
        from app.engine.analyzers.url_analyzer import analyze_url  # type: ignore
        return analyze_url(url_str)
    except ImportError:
        pass

    # // PENDING url_analyzer: Static fallback placeholder
    indicators: list[Indicator] = []
    legitimacy: list[LegitimacySignal] = []

    clean_url = url_str.strip()
    parsed = urlparse(clean_url if "://" in clean_url else "http://" + clean_url)
    hostname = (parsed.hostname or "").lower()

    # Static heuristic 1: Known deceptive / phishing patterns in test set
    if re.search(r"(?:sbi|hdfc|icici|yono|kyc|bank)[-_a-z0-9]*\.(?:xyz|top|verify|support|info)", hostname):
        indicators.append(
            Indicator(
                code="DECEPTIVE_URL_DETECTED",
                label="Deceptive brand or banking lookalike domain in QR destination",
                severity="high",
                weight=0.75,
                evidence=hostname,
            )
        )
        if any(term in clean_url.lower() for term in ["kyc", "login", "update", "verify", "pan"]):
            indicators.append(
                Indicator(
                    code="KYC_COERCION",
                    label="Credential or KYC update solicitation in URL path",
                    severity="high",
                    weight=0.60,
                    evidence=clean_url,
                )
            )

    # Static heuristic 2: URL Shortener hiding real destination
    shorteners = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "rb.gy"}
    if hostname in shorteners:
        indicators.append(
            Indicator(
                code="URL_SHORTENER_DETECTED",
                label="Obfuscated URL shortener hiding true destination",
                severity="low",
                weight=0.30,
                evidence=hostname,
            )
        )

    # Static heuristic 3: Genuine official banking or government domain
    if hostname in ("sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "cybercrime.gov.in", "incometax.gov.in"):
        legitimacy.append(
            LegitimacySignal(
                code="LEGIT_OFFICIAL_DOMAIN",
                label="Destination points to verified official organization domain",
                weight=0.80,
                evidence=hostname,
            )
        )

    return {
        "indicators": indicators,
        "legitimacy_signals": legitimacy,
        "hostname": hostname,
    }


def analyze_qr_payload(payload: str) -> dict[str, Any]:
    """
    Performs comprehensive analysis on a decoded QR payload.
    Classifies type (upi / url / text / wifi / other) and applies threat detection rules.
    ARCHITECTURE 8.8 & BUILD_PLAN Chunk 9.
    Never opens or visits destinations.
    """
    stripped_payload = (payload or "").strip()
    if not stripped_payload:
        return {
            "scan_type": "qr",
            "payload": "",
            "payload_type": "other",
            "risk": {"score": 0, "level": "unable_to_verify", "label": "Unable to Verify"},
            "confidence": 0.50,
            "verification_status": "unable_to_verify",
            "category": {"code": "unverifiable", "label": "Unverifiable Content"},
            "summary": "QR payload is empty or unreadable.",
            "indicators": [],
            "legitimacy_signals": [],
            "recommendations": ["Do not interact with damaged or illegible QR codes."],
            "verify_steps": ["Inspect the physical QR code for tampering or stickers pasted over genuine codes."],
            "extracted": {"qr": None, "upi": None, "urls": []},
            "engine_version": "2.0.0",
        }

    payload_type = classify_payload(stripped_payload)
    risk_indicators: list[Indicator] = []
    legitimacy_signals: list[LegitimacySignal] = []

    extracted_upi: dict[str, Any] | None = None
    extracted_urls: list[dict[str, Any]] = []

    # --------------------------------------------------------------------------
    # Case 1: UPI Payment URI (upi://pay?...)
    # --------------------------------------------------------------------------
    if payload_type == "upi":
        upi_info = parse_upi_uri(stripped_payload)
        extracted_upi = upi_info

        vpa = upi_info.get("vpa") or ""
        payee_name = upi_info.get("payee_name") or ""
        amount = upi_info.get("amount")
        note = upi_info.get("note") or ""
        vpa_handle = upi_info.get("vpa_handle") or ""

        # Flag 1: Pre-filled payment amount on alleged reward or refund
        # Scammers request money from the victim while claiming it is a reward/refund
        reward_in_note = _contains_reward_claim(note)
        reward_in_name = _contains_reward_claim(payee_name)
        if amount is not None and amount > 0 and (reward_in_note or reward_in_name):
            claim_text = reward_in_note or reward_in_name
            evidence_snippet = f"Pre-filled amount ₹{amount:g} with claim '{claim_text}' (Note: '{note}')"
            risk_indicators.append(
                Indicator(
                    code="UPI_PREFILLED_AMOUNT_REWARD_TRAP",
                    label="Pre-filled debit amount on alleged reward, cashback, or refund QR code",
                    severity="high",
                    weight=0.75,
                    evidence=evidence_snippet,
                )
            )

        # Flag 2: "Scan to receive money" / UPI PIN to receive deception
        # Receiving money in UPI never requires scanning a QR or entering a PIN
        receive_note_match = _detect_scan_to_receive(note)
        receive_name_match = _detect_scan_to_receive(payee_name)
        if receive_note_match or receive_name_match:
            evidence_phrase = receive_note_match or receive_name_match
            risk_indicators.append(
                Indicator(
                    code="UPI_SCAN_TO_RECEIVE_FRAUD",
                    label="'Scan to receive' deception: receiving UPI funds never requires scanning a QR code or entering a PIN",
                    severity="high",
                    weight=0.80,
                    evidence=evidence_phrase,
                )
            )

        # Flag 3: Payee name claims official entity / brand with personal retail handle
        claimed_brand = claims_brand_or_authority(payee_name)
        if claimed_brand and is_personal_handle(vpa_handle):
            risk_indicators.append(
                Indicator(
                    code="UPI_IMPERSONATION_PERSONAL_HANDLE",
                    label=f"Payee name claims official entity ('{claimed_brand.title()}') but routes to individual retail UPI handle",
                    severity="high",
                    weight=0.65,
                    evidence=f"Payee: '{payee_name}' | VPA: '{vpa}'",
                )
            )

        # Flag 4: High urgency pressure in note text
        urgent_match = _detect_urgent_note(note)
        if urgent_match:
            risk_indicators.append(
                Indicator(
                    code="UPI_URGENT_NOTE_PRESSURE",
                    label="High urgency or intimidation language in payment description",
                    severity="high",
                    weight=0.50,
                    evidence=f"Note: '{note}'",
                )
            )

        # Flag 5: Run note text (tn) through existing message detection engine
        if note:
            try:
                from app.engine import engine as message_engine
                msg_analysis = message_engine.analyze(note)
                for ind_dict in msg_analysis.get("indicators", []):
                    code = ind_dict.get("code")
                    # Avoid duplicate codes
                    if not any(r.code == code for r in risk_indicators):
                        risk_indicators.append(
                            Indicator(
                                code=code,
                                label=f"Note content indicator: {ind_dict.get('label', '')}",
                                severity=ind_dict.get("severity", "medium"),
                                weight=ind_dict.get("weight", 0.40),
                                evidence=ind_dict.get("evidence", note),
                            )
                        )
            except (ImportError, AttributeError, KeyError, ValueError, TypeError):
                pass

        # Legitimacy check for UPI: Verified merchant or standard peer payment without threats
        if not risk_indicators:
            # Check if clean merchant handle
            merchant_handles = ("icici", "hdfcbank", "sbi", "axisbank", "razorpay")
            if vpa_handle in merchant_handles or not is_personal_handle(vpa_handle):
                legitimacy_signals.append(
                    LegitimacySignal(
                        code="LEGIT_MERCHANT_UPI_VPA",
                        label="Registered merchant UPI VPA with no deceptive signals",
                        weight=0.50,
                        evidence=vpa,
                    )
                )
            else:
                legitimacy_signals.append(
                    LegitimacySignal(
                        code="LEGIT_STANDARD_UPI_PAYMENT",
                        label="Standard UPI payment string with clean parameters",
                        weight=0.35,
                        evidence=vpa,
                    )
                )

    # --------------------------------------------------------------------------
    # Case 2: URL Payload
    # --------------------------------------------------------------------------
    elif payload_type == "url":
        url_analysis = analyze_url_payload(stripped_payload)
        risk_indicators.extend(url_analysis.get("indicators", []))
        legitimacy_signals.extend(url_analysis.get("legitimacy_signals", []))
        extracted_urls.append({
            "raw": stripped_payload,
            "normalized": stripped_payload,
            "is_deceptive": any(i.code == "DECEPTIVE_URL_DETECTED" for i in risk_indicators),
        })

    # --------------------------------------------------------------------------
    # Case 3: Wi-Fi Configuration (WIFI:S:...;P:...;;)
    # --------------------------------------------------------------------------
    elif payload_type == "wifi":
        legitimacy_signals.append(
            LegitimacySignal(
                code="LEGIT_WIFI_CONFIG",
                label="Standard local Wi-Fi network configuration QR code",
                weight=0.75,
                evidence=stripped_payload[:30],
            )
        )

    # --------------------------------------------------------------------------
    # Case 4: Plain Text Payload
    # --------------------------------------------------------------------------
    elif payload_type == "text":
        try:
            from app.engine import engine as message_engine
            msg_res = message_engine.analyze(stripped_payload)
            for ind in msg_res.get("indicators", []):
                risk_indicators.append(
                    Indicator(
                        code=ind["code"],
                        label=ind["label"],
                        severity=ind["severity"],
                        weight=ind["weight"],
                        evidence=ind.get("evidence"),
                    )
                )
            for leg in msg_res.get("legitimacy_signals", []):
                legitimacy_signals.append(
                    LegitimacySignal(
                        code=leg["code"],
                        label=leg["label"],
                        weight=leg["weight"],
                        evidence=leg.get("evidence"),
                    )
                )
        except (ImportError, AttributeError, KeyError, ValueError, TypeError):
            pass

    # --------------------------------------------------------------------------
    # Scoring computation using Noisy-OR formulation (ARCHITECTURE Section 8.5)
    # --------------------------------------------------------------------------
    score_data = calculate_score(
        risk_indicators=risk_indicators,
        legitimacy_signals=legitimacy_signals,
        intel_hits=0,
        is_unusable=False,
    )

    risk_score = score_data["score"]
    risk_level = score_data["level"]
    risk_label = score_data["label"]

    # Category determination tailored for QR and UPI
    if any(i.code in ("UPI_PREFILLED_AMOUNT_REWARD_TRAP", "UPI_SCAN_TO_RECEIVE_FRAUD") for i in risk_indicators):
        category = {"code": "qr_reward_scam", "label": "Potential QR / Reward Scam"}
    elif any(i.code == "UPI_IMPERSONATION_PERSONAL_HANDLE" for i in risk_indicators):
        category = {"code": "upi_pin_fraud", "label": "UPI Impersonation / Collect Request Scam"}
    elif any(i.code == "DECEPTIVE_URL_DETECTED" for i in risk_indicators):
        category = {"code": "phishing_link", "label": "Deceptive QR / Phishing Website"}
    elif payload_type == "wifi":
        category = {"code": "wifi_config", "label": "Wi-Fi Network Configuration"}
    elif risk_level == "likely_safe":
        category = {"code": "legitimate_communication", "label": "Likely Legitimate Communication"}
    else:
        category = score_data.get("category", {"code": "suspicious_communication", "label": "Suspicious Communication"})

    # Dynamic summary built strictly from detected signals
    if risk_indicators:
        threat_summaries = [f"{i.label} ({i.evidence or ''})" for i in risk_indicators]
        summary = (
            f"Threats Detected ({risk_label}): This QR code exhibits high-risk indicators: "
            + "; ".join(threat_summaries[:3])
            + "."
        )
    elif payload_type == "wifi":
        summary = "Likely Safe: Valid Wi-Fi network configuration QR code for connecting to a local wireless network."
    elif payload_type == "upi":
        summary = f"Likely Safe: Standard UPI payment QR code addressed to {extracted_upi.get('vpa', 'payee')} with no deceptive indicators."
    elif payload_type == "url":
        summary = "Likely Safe: QR code contains a standard web link without known deceptive indicators."
    else:
        summary = "Likely Safe: Plain text QR code with no suspicious or fraudulent patterns detected."

    # Actionable safety recommendations
    recommendations = []
    if payload_type == "upi":
        recommendations.append("NEVER enter your UPI PIN to receive money. UPI PIN is only used to deduct money from your account.")
        if any(i.code == "UPI_PREFILLED_AMOUNT_REWARD_TRAP" for i in risk_indicators):
            recommendations.append("DO NOT approve this payment request. Scanning this code will send money to the requester.")
        recommendations.append("Always verify the verified merchant name and VPA in your UPI app before completing payment.")
    elif payload_type == "url":
        recommendations.append("Do not open untrusted or unverified links from scanned QR codes.")
        recommendations.append("Type the organization's official website address directly into your browser.")
    elif payload_type == "wifi":
        recommendations.append("Only connect to trusted Wi-Fi networks in secure physical environments.")
    else:
        recommendations.append("Verify the origin and physical context of this QR code before taking action.")

    verify_steps = [
        "Inspect physical QR stickers at shops to confirm they have not been overlaid or replaced with fraudulent codes.",
        "Check that the recipient name in your payment app matches the physical store or entity you intend to pay.",
        "Remember that genuine lottery prizes, tax refunds, and cashback rewards never require scanning a QR code to collect.",
    ]

    verification_status = "unverified"
    if any(i.code == "DECEPTIVE_URL_DETECTED" for i in risk_indicators):
        verification_status = "unverified_deceptive_destination"

    confidence = 0.90 if risk_indicators or legitimacy_signals else 0.75

    return {
        "scan_type": "qr",
        "payload": stripped_payload,
        "payload_type": payload_type,
        "risk": {
            "score": risk_score,
            "level": risk_level,
            "label": risk_label,
        },
        "confidence": confidence,
        "verification_status": verification_status,
        "category": category,
        "summary": summary,
        "indicators": [ind.to_dict() for ind in risk_indicators],
        "legitimacy_signals": [leg.to_dict() for leg in legitimacy_signals],
        "recommendations": recommendations,
        "verify_steps": verify_steps,
        "extracted": {
            "qr": {
                "payload": stripped_payload,
                "payload_type": payload_type,
            },
            "upi": extracted_upi,
            "urls": extracted_urls,
        },
        "engine_version": "2.0.0",
    }


def analyze_qr_image(image_bytes: bytes) -> dict[str, Any]:
    """
    Decodes and analyzes an in-memory QR image.
    Validates magic bytes and size (<= 5 MB). Never saves image to disk.
    Per ARCHITECTURE 8.8.
    """
    validate_qr_image(image_bytes)
    payload = decode_qr_image(image_bytes)
    if not payload:
        return {
            "scan_type": "qr",
            "payload": None,
            "payload_type": "other",
            "risk": {"score": 0, "level": "unable_to_verify", "label": "Unable to Verify"},
            "confidence": 0.50,
            "verification_status": "unable_to_verify",
            "category": {"code": "unverifiable", "label": "Unverifiable Content"},
            "summary": "Unable to Verify: No QR code could be decoded from the uploaded image. The image may be blurry, damaged, or empty.",
            "indicators": [],
            "legitimacy_signals": [],
            "recommendations": ["Ensure the QR code is clearly focused and well-lit before re-uploading."],
            "verify_steps": ["Do not attempt to pay using damaged or partially obscured QR codes."],
            "extracted": {"qr": None, "upi": None, "urls": []},
            "engine_version": "2.0.0",
        }

    return analyze_qr_payload(payload)
