"""
GARUDA UPI Analyzer
===================
Analyzes UPI payment links (upi://pay?...) and QR payloads for signs of fraud,
brand impersonation, collect request traps, and bait notes - WITHOUT initiating
any transaction or network requests (static analysis only).

How it works:
  1. parse_upi()     -> extract and URL-decode parameters (pa, pn, am, tn),
                        validate that pa is in 'name@handle' format.
  2. run checks      -> detect brand impersonation, pre-filled amounts,
                        bait notes, unknown/suspicious PSP handles.
  3. noisy-OR score  -> combine indicator weights into a 0-100 risk score
                        (weights 0.1 - 0.85, never "critical").
  4. build result    -> level, category, summary, and safety advice.

Only Python's standard library is used, so nothing extra to install.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, unquote_plus, urlsplit

ENGINE_VERSION = "upi-1.0.0"

# ---------------------------------------------------------------------------
# 1. Reference lists & constants
# ---------------------------------------------------------------------------

# Common recognized UPI PSP handles issued by major Indian banks and payment apps
COMMON_HANDLES = {
    # Specifically required common handles:
    "ybl", "ibl", "axl", "okaxis", "oksbi", "okhdfcbank", "okicici",
    "paytm", "ptyes", "apl", "upi",
    # Other widely used official bank and wallet handles:
    "okhdfc", "okbizaxis", "barodampay", "icici", "sbi", "hdfc", "axisbank",
    "kotak", "postbank", "pingpay", "idfcbank", "idfcfirst", "federal", "indus",
    "pnb", "cnrb", "unionbank", "aubank", "freecharge", "airtel", "yesbank", "ikwik",
}

# Bank, brand, government, refund, kyc, and reward keywords scammers use to impersonate
BRAND_TERMS = {
    # Banks & Financial institutions
    "sbi", "statebank", "onlinesbi", "hdfc", "hdfcbank", "icici", "icicibank",
    "axis", "axisbank", "kotak", "pnb", "punjabnational", "bob", "bankofbaroda",
    "canara", "canarabank", "unionbank", "yesbank", "indusind", "idfc", "rbi",
    "bank", "netbanking", "banking",
    # Major tech / payment brands
    "paytm", "phonepe", "gpay", "googlepay", "bhim", "amazon", "amazonpay",
    "flipkart", "airtel", "airtelpayments", "jio", "jiomoney", "netflix", "irctc",
    # Government, regulators & utility authorities
    "govt", "government", "gov", "uidai", "aadhaar", "incometax", "itdept",
    "cybercrime", "police", "challan", "dept", "department", "authority",
    "sebi", "epfo", "electricity", "bijli", "discom", "vidyut",
    # Refund & reversal claims
    "refund", "cashback", "reversal",
    # KYC / Account status coercion
    "kyc", "verification", "verify", "update", "support", "helpline", "care",
    "customercare", "service", "security", "blocked", "suspended",
    # Reward / lottery / gift deception
    "reward", "rewards", "prize", "lottery", "winner", "gift", "bonus", "inam",
    "puraskar", "cashprize",
}

# Bait keywords in transaction notes (English + Hindi/Telugu romanized)
# Scammers use these to fool victims into believing they are receiving money
BAIT_NOTE_TERMS = [
    # English
    "refund", "refunds", "refunded", "prize", "prizes", "cashback", "cash back",
    "receive", "received", "receiving", "receiver", "won", "winner", "winning",
    "reward", "rewards", "lottery", "bonus", "claim", "claimed", "gift",
    "credited", "lucky draw", "accept",
    # Hindi (romanized)
    "inam", "inaam", "puraskar", "jeet", "jeeto", "jeeta", "jete",
    "milega", "milenge", "lelo", "le lo", "lena", "paise lo", "paise le",
    "prapt", "prapti", "wapas", "wapsi", "vapasi", "dhan", "bhediye",
    # Telugu (romanized)
    "geluchukondi", "gelicharu", "gelupu", "bahumathi", "pondandi",
    "teesukondi", "teesuko", "vastundi", "vastayi", "vasthundhi",
    "dabbulu", "tirigi", "venakki", "ravali",
]

ALWAYS_RECOMMENDATION = "Scanning a QR code can only SEND money, never receive it."


# ---------------------------------------------------------------------------
# 2. Data classes
# ---------------------------------------------------------------------------

@dataclass
class Indicator:
    code: str
    label: str
    severity: str      # low | medium | high
    weight: float      # 0.1 - 0.85
    evidence: str


class ParsedUpi(dict):
    """
    Parsed UPI payment payload supporting both dictionary lookup
    (data['pa']) and attribute access (data.pa).
    """
    def __init__(
        self,
        valid: bool,
        pa: str | None = None,
        pn: str | None = None,
        am: float | None = None,
        tn: str | None = None,
        handle: str | None = None,
        username: str | None = None,
        params: dict[str, str] | None = None,
        error: str | None = None,
        raw: str = "",
    ):
        super().__init__(
            valid=valid,
            pa=pa,
            pn=pn,
            am=am,
            tn=tn,
            handle=handle,
            username=username,
            params=params or {},
            error=error,
            raw=raw,
        )

    def __getattr__(self, name: str):
        if name in self:
            return self[name]
        raise AttributeError(f"'ParsedUpi' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value

    def to_dict(self) -> dict:
        return dict(self)


@dataclass
class UpiResult:
    input: str
    valid: bool
    pa: str | None = None
    pn: str | None = None
    am: float | None = None
    tn: str | None = None
    handle: str | None = None
    username: str | None = None
    score: int = 0
    level: str = "unable_to_verify"
    label: str = "Unable to Verify"
    category: str = "none"
    category_label: str = ""
    summary: str = ""
    indicators: list[Indicator] = field(default_factory=list)
    legitimacy_signals: list[Indicator] = field(default_factory=list)
    verification_status: str = "unverified"
    recommendations: list[str] = field(default_factory=list)
    error: str | None = None
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["indicators"] = [i.__dict__ for i in self.indicators]
        d["legitimacy_signals"] = [i.__dict__ for i in self.legitimacy_signals]
        return d


# ---------------------------------------------------------------------------
# 3. Parsing & Validation
# ---------------------------------------------------------------------------

def parse_upi(text: str) -> ParsedUpi:
    """
    Parse a UPI payment URI (upi://pay?pa=&pn=&am=&tn=...).
    URL-decodes parameter values and validates that 'pa' is a valid 'name@handle'.
    """
    raw = (text or "").strip()
    if not raw:
        return ParsedUpi(valid=False, error="Please provide a UPI payment link or QR payload.", raw=raw)

    candidate = raw
    # If the entire input was percent-encoded, decode it once first
    if candidate.lower().startswith("upi%3a"):
        candidate = unquote_plus(candidate)

    if not candidate.lower().startswith("upi://"):
        return ParsedUpi(valid=False, error="URI does not use the upi:// scheme.", raw=raw)

    parts = urlsplit(candidate)
    query_str = parts.query
    if not query_str and "?" in candidate:
        query_str = candidate.split("?", 1)[1]

    raw_params = parse_qs(query_str, keep_blank_values=True)
    params: dict[str, str] = {}
    for k, v_list in raw_params.items():
        if v_list:
            params[k.lower()] = unquote_plus(v_list[0]).strip()

    pa = params.get("pa", "").strip()
    pn = params.get("pn", "").strip()
    tn = params.get("tn", "").strip()
    am_raw = params.get("am", "").strip()

    # Validate pa as name@handle
    if not pa or "@" not in pa:
        return ParsedUpi(
            valid=False,
            pa=pa or None,
            pn=pn or None,
            tn=tn or None,
            params=params,
            error=f"Invalid UPI address '{pa}' (must be in format name@handle).",
            raw=raw,
        )

    vpa_parts = pa.split("@")
    if len(vpa_parts) != 2:
        return ParsedUpi(
            valid=False,
            pa=pa,
            pn=pn or None,
            tn=tn or None,
            params=params,
            error=f"Invalid UPI address '{pa}' (must contain exactly one '@').",
            raw=raw,
        )

    username, handle = vpa_parts[0].strip(), vpa_parts[1].strip().lower()
    if not username or not handle:
        return ParsedUpi(
            valid=False,
            pa=pa,
            pn=pn or None,
            tn=tn or None,
            params=params,
            error=f"Invalid UPI address '{pa}' (name and handle cannot be empty).",
            raw=raw,
        )

    if not re.match(r"^[a-zA-Z0-9.\-_]+$", username):
        return ParsedUpi(
            valid=False,
            pa=pa,
            pn=pn or None,
            tn=tn or None,
            params=params,
            error=f"Invalid characters in UPI username '{username}'.",
            raw=raw,
        )

    if not re.match(r"^[a-zA-Z0-9.\-]+$", handle):
        return ParsedUpi(
            valid=False,
            pa=pa,
            pn=pn or None,
            tn=tn or None,
            params=params,
            error=f"Invalid characters in UPI handle '{handle}'.",
            raw=raw,
        )

    # Parse amount
    amount: float | None = None
    if am_raw:
        try:
            amount = float(am_raw)
        except ValueError:
            clean_am = re.sub(r"[^\d.]", "", am_raw)
            if clean_am:
                try:
                    amount = float(clean_am)
                except ValueError:
                    amount = None

    return ParsedUpi(
        valid=True,
        pa=pa,
        pn=pn or None,
        am=amount,
        tn=tn or None,
        handle=handle,
        username=username,
        params=params,
        error=None,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# 4. Scoring & Bands
# ---------------------------------------------------------------------------

def noisy_or(weights: list[float]) -> float:
    """Combine weights: 1 - (1-w1)(1-w2)... -> never exceeds 1, grows with each signal."""
    p = 1.0
    for w in weights:
        p *= (1.0 - w)
    return 1.0 - p


def band(score: int) -> tuple[str, str]:
    """
    Returns (risk_level, risk_label).
    Strictly follows url_analyzer bands and NEVER returns 'critical'.
    """
    if score >= 65:
        return "high", "High Risk"
    if score >= 45:
        return "medium", "Medium Risk"
    if score >= 25:
        return "suspicious", "Suspicious"
    return "likely_safe", "Likely Safe"


# ---------------------------------------------------------------------------
# 5. The Main Analyzer
# ---------------------------------------------------------------------------

def analyze_upi(raw: str) -> UpiResult:
    """
    Analyzes a UPI payment link/string and returns risk assessment,
    score, indicators, and safety recommendations.
    """
    parsed = parse_upi(raw)
    if not parsed.valid:
        res = UpiResult(
            input=raw,
            valid=False,
            pa=parsed.pa,
            pn=parsed.pn,
            tn=parsed.tn,
            score=0,
            level="unable_to_verify",
            label="Unable to Verify",
            category="unverifiable",
            category_label="Unverifiable UPI Link",
            summary="GARUDA could not verify this input because it is not a valid UPI payment link.",
            error=parsed.error or "Invalid UPI address (must be name@handle).",
            recommendations=[
                ALWAYS_RECOMMENDATION,
                "Make sure you scanned a complete, undamaged UPI QR code or valid payment link.",
            ],
        )
        return res

    res = UpiResult(
        input=raw,
        valid=True,
        pa=parsed.pa,
        pn=parsed.pn,
        am=parsed.am,
        tn=parsed.tn,
        handle=parsed.handle,
        username=parsed.username,
    )
    ind = res.indicators

    # --- Indicator 1: UPI_BRAND_IMPERSONATION -------------------------------
    # Check bank, brand, govt, refund, kyc, or reward words in pa (username) or pn
    username_lower = (parsed.username or "").lower()
    user_tokens = set(re.split(r"[.\-_0-9]+", username_lower))

    matched_pa = []
    for term in BRAND_TERMS:
        if term in user_tokens:
            matched_pa.append(term)
        elif len(term) >= 4 and term in username_lower:
            matched_pa.append(term)

    pn_lower = (parsed.pn or "").lower()
    pn_words = set(re.findall(r"[a-zA-Z0-9]+", pn_lower))
    matched_pn = []
    for term in BRAND_TERMS:
        if " " in term and term in pn_lower:
            matched_pn.append(term)
        elif term in pn_words:
            matched_pn.append(term)
        elif len(term) >= 4 and re.search(rf"\b{re.escape(term)}\b", pn_lower):
            matched_pn.append(term)

    if matched_pa or matched_pn:
        evidence_items = []
        if matched_pa:
            evidence_items.append(f"pa matches '{matched_pa[0]}'")
        if matched_pn:
            evidence_items.append(f"pn matches '{matched_pn[0]}'")
        ind.append(
            Indicator(
                code="UPI_BRAND_IMPERSONATION",
                label="Payee address or name uses bank, brand, government, refund, or KYC words",
                severity="high",
                weight=0.65,
                evidence="; ".join(evidence_items),
            )
        )

    # --- Indicator 2: UPI_PREFILLED_AMOUNT ----------------------------------
    # Pre-filled amount (higher weight if >= 2000)
    if parsed.am is not None and parsed.am > 0:
        if parsed.am >= 2000:
            ind.append(
                Indicator(
                    code="UPI_PREFILLED_AMOUNT",
                    label=f"Pre-filled debit amount of ₹{parsed.am:g} (>= ₹2,000)",
                    severity="medium",
                    weight=0.40,
                    evidence=f"am={parsed.am:g}",
                )
            )
        else:
            ind.append(
                Indicator(
                    code="UPI_PREFILLED_AMOUNT",
                    label=f"Pre-filled debit amount of ₹{parsed.am:g}",
                    severity="low",
                    weight=0.15,
                    evidence=f"am={parsed.am:g}",
                )
            )

    # --- Indicator 3: UPI_BAIT_NOTE -----------------------------------------
    # Bait words in transaction note (refund/prize/cashback/receive/won, incl. Hindi/Telugu)
    if parsed.tn:
        tn_lower = parsed.tn.lower()
        matched_bait = []
        for term in BAIT_NOTE_TERMS:
            if " " in term:
                if term in tn_lower:
                    matched_bait.append(term)
            else:
                if re.search(rf"\b{re.escape(term)}\b", tn_lower):
                    matched_bait.append(term)

        if matched_bait:
            ind.append(
                Indicator(
                    code="UPI_BAIT_NOTE",
                    label=f"Transaction note uses bait or claim wording ('{matched_bait[0]}')",
                    severity="high",
                    weight=0.55,
                    evidence=f"tn='{parsed.tn}' matches '{matched_bait[0]}'",
                )
            )

    # --- Indicator 4: UPI_UNKNOWN_HANDLE ------------------------------------
    # Not a common PSP handle like ybl, ibl, axl, okaxis, oksbi, okhdfcbank, etc.
    handle = (parsed.handle or "").lower()
    if handle not in COMMON_HANDLES:
        ind.append(
            Indicator(
                code="UPI_UNKNOWN_HANDLE",
                label=f"Unrecognized or uncommon UPI handle '@{handle}'",
                severity="medium",
                weight=0.30,
                evidence=f"Handle '@{handle}' is not among widely recognized PSP handles",
            )
        )
    else:
        if not ind:
            res.legitimacy_signals.append(
                Indicator(
                    code="LEGIT_COMMON_PSP",
                    label="Uses a standard recognized UPI PSP handle",
                    severity="low",
                    weight=0.0,
                    evidence=f"@{handle}",
                )
            )
            res.verification_status = "standard_psp_handle"

    # --- Scoring & Categorization -------------------------------------------
    res.score = round(100 * noisy_or([i.weight for i in ind]))
    res.level, res.label = band(res.score)

    if any(i.code == "UPI_BRAND_IMPERSONATION" for i in ind):
        res.category = "upi_brand_impersonation"
        res.category_label = "UPI Brand / Authority Impersonation"
    elif any(i.code in ("UPI_BAIT_NOTE", "UPI_PREFILLED_AMOUNT") for i in ind):
        res.category = "upi_collect_scam"
        res.category_label = "UPI Advance Fee / Collect Scam"
    elif ind:
        res.category = "suspicious_upi"
        res.category_label = "Suspicious UPI Payment"
    else:
        res.category = "none"
        res.category_label = "Likely Legitimate UPI"

    # --- Summary & Recommendations ------------------------------------------
    res.summary = _summary(res)
    res.recommendations = _advice(res)
    return res


def _summary(res: UpiResult) -> str:
    if not res.indicators:
        return (
            f"This UPI payment link ({res.pa}) uses a standard handle and shows no deceptive indicators. "
            "Always verify the payee before confirming payment."
        )
    reasons = "; ".join(i.label.lower() for i in res.indicators[:3])
    return f"This UPI link shows warning signs: {reasons}."


def _advice(res: UpiResult) -> list[str]:
    advice = [ALWAYS_RECOMMENDATION]
    if res.level == "high":
        advice.extend([
            "Do NOT approve this payment or enter your UPI PIN.",
            "Entering your UPI PIN will DEBIT money from your bank account, not credit it.",
            "If you were promised a refund, lottery prize, or reward, this is a scam.",
            "Report fraudulent UPI IDs at cybercrime.gov.in or call helpline 1930.",
        ])
    elif res.level in ("medium", "suspicious"):
        advice.extend([
            "Verify the recipient's identity independently before sending funds.",
            "Never enter your UPI PIN unless you intend to send money.",
        ])
    else:
        advice.extend([
            "Only proceed if you know and trust this payee.",
            "Never share your UPI PIN or OTP with anyone.",
        ])
    return advice


if __name__ == "__main__":
    test_samples = [
        "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received",
        "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
        "upi://pay?pa=abc",
        "upi://pay?pa=customercare@obscurebank&pn=Airtel Support&am=2500&tn=dabbulu teesukondi",
    ]
    for s in test_samples:
        r = analyze_upi(s)
        print(f"{s[:55]:55} -> Score: {r.score:2} | Level: {r.level:16} | Indicators: {len(r.indicators)}")
