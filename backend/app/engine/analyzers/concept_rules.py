import re
import os
from typing import List, Dict, Any, Optional, Tuple
import yaml

from app.engine.analyzers.text_rules import Indicator, extract_evidence_snippet

# Path to concepts lexicon
LEXICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lexicons", "concepts.yaml")

_CONCEPTS_CACHE: Optional[Dict[str, Any]] = None


def load_concepts() -> Dict[str, Any]:
    global _CONCEPTS_CACHE
    if _CONCEPTS_CACHE is None:
        try:
            with open(LEXICON_PATH, "r", encoding="utf-8") as f:
                _CONCEPTS_CACHE = yaml.safe_load(f) or {}
        except Exception:
            _CONCEPTS_CACHE = {}
    return _CONCEPTS_CACHE


def find_lexicon_match(terms: List[str], text: str) -> Optional[Tuple[str, int, int]]:
    """Searches for terms in text matching on word boundaries."""
    for term in terms:
        # Match as word boundary if ASCII, or simple substring if Indic script
        is_indic = any("\u0900" <= c <= "\u097f" or "\u0c00" <= c <= "\u0c7f" for c in term)
        if is_indic:
            idx = text.find(term.lower())
            if idx != -1:
                return term, idx, idx + len(term)
        else:
            pat = r"\b" + re.escape(term) + r"\b"
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return term, m.start(), m.end()
    return None


NEGATION_WORDS = [
    "do not", "don't", "dont", "never", "not", "mat", "na",
    "kisi ko nahi", "kisi ko mat", "వద్దు", "లేదు", "చెప్పకండి",
    "नहीं", "मत", "ना", "साझा न करें"
]


def is_negated_phrase(text: str, start: int) -> bool:
    """Checks if the phrase is preceded by an authentic warning or negative qualifier."""
    prefix = text[max(0, start - 35):start].lower()
    return any(neg in prefix for neg in NEGATION_WORDS)


# Semantic concept matchers for multi-token actions
AMOUNT_REGEX = re.compile(
    r"(?:[₹$€£]|rs\.?|inr)\s*[\d,]+(?:\.\d+)?|\b\d+\s*(?:lakh|crore|thousand|bonus)\b",
    re.IGNORECASE
)

FEE_DEMAND_PATTERNS = [
    r"\b(?:pay|deposit|send|bharo|kattandi|transfer)\s+.*?(?:fee|charges|processing|gst|tax|registration|deposit|redelivery|release)\b",
    r"\b(?:fee|charges|tax|gst)\s+(?:bharo|kattandi|do|pay|bhar)\b",
    r"\bfee\s+(?:of\s+)?[₹$]?[\d,]+\b",
    r"\bto\s+unlock\s+vip\s+tasks\s+deposit\b",
    r"\bprocessing\s+fee\b",
]

CREDENTIAL_REQUEST_PATTERNS = [
    r"\b(?:share|send|tell|enter|cheppandi|bhejo|saajha|batao|provide|submit|re-?enter)\s+.*?(?:otp|pin|password|cvv|card\s+details|bank\s+details|aadhaar|pan)\b",
    r"\bsh[a@]re\s+y[o0]ur\s+[o0]tp\b",
    r"\bmee\s+upi\s+pin\s+enter\s+cheyandi\b",
    r"\bअपना\s+otp\s+साझा\s+करें\b",
    r"\bమీ\s+otp\s+చెప్పండి\b",
    r"\bapprove\s+(?:the\s+)?request\s+on\s+your\s+upi\s+app\b",
    r"\benter\s+(?:your\s+)?pin\s+to\s+receive\b",
    r"\bsend\s+your\s+aadhaar\b",
    r"\bupdate\s+pan\s+immediately\b",
    r"\bkyc\s+update\s+ke\s+liye\b",
    r"\bkyc\s+అప్‌డేట్\s+కోసం\b",
    r"\bkyc\s+अपडेट\s+करने\s+के\s+लिए\b",
]

CONTACT_CTA_PATTERNS = [
    r"\b(?:call|calling|whatsapp|contact)\s+(?:our\s+officer\s+|officer\s+|hr\s+|us\s+at\s+)?(?:\+?91[\s-]?)?[6-9]\d{9}\b",
    r"\bcontact\s+(?:hr\s+)?(?:on\s+)?(?:telegram|whatsapp|phone)\s+@?[a-z0-9_]+\b",
    r"\b(?:click|open|visit)\s+(?:this\s+|here\s+|the\s+)?(?:link|url)\b",
    r"\bscan\s+(?:this\s+)?qr\b",
    r"\bredeem\s+now\b",
    r"\bcomplete\s+kyc\s+by\s+calling\b",
    r"\bcall\s+our\s+officer\b",
    r"\bturant\s+is\s+number\s+pe\s+call\b",
    r"इस\s+नंबर\s+पर\s+कॉल",
    r"नंबर\s+पर\s+कॉल\s+करें",
    r"\bee\s+link\s+(?:lo|click)\b",
    r"लिंक\s+पर\s+क्लिक",
    r"లింక్\s+క్లిక్",
]

FAMILY_EMERGENCY_PATTERNS = [
    r"\bhi\s+mom,\s+this\s+is\s+my\s+new\s+number\b",
    r"\bmy\s+phone\s+broke\b",
    r"\bsend\s+[₹$]?[\d,]+\s+urgently\s+to\b",
    r"\bhelp\.urgent@ybl\b",
]


def analyze_concept_combinations(search_text: str, original_text: str) -> List[Indicator]:
    """
    Evaluates order-independent combinations of conceptual signals per ARCHITECTURE Section 8.
    Produces high-fidelity indicators with concept-grounded evidence snippets.
    """
    concepts = load_concepts()
    indicators: List[Indicator] = []

    # 1. Match individual concepts
    asset_match = find_lexicon_match(concepts.get("ASSET", {}).get("terms", []), search_text)
    threat_match = find_lexicon_match(concepts.get("THREAT", {}).get("terms", []), search_text)
    urgency_match = find_lexicon_match(concepts.get("URGENCY", {}).get("terms", []), search_text)
    reward_match = find_lexicon_match(concepts.get("REWARD", {}).get("terms", []), search_text)
    auth_match = find_lexicon_match(concepts.get("AUTHORITY", {}).get("terms", []), search_text)
    inv_match = find_lexicon_match(concepts.get("INVESTMENT_JOB", {}).get("terms", []), search_text)

    # 2. Match regex-based concept actions
    amount_m = AMOUNT_REGEX.search(search_text)
    amount_match = (amount_m.group(0), amount_m.start(), amount_m.end()) if amount_m else None

    # Fee demand match
    fee_match = None
    for pat in FEE_DEMAND_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            fee_match = (m.group(0), m.start(), m.end())
            break

    # Credential request match (with negation check)
    cred_match = None
    for pat in CREDENTIAL_REQUEST_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            if not is_negated_phrase(search_text, m.start()):
                cred_match = (m.group(0), m.start(), m.end())
                break

    # Contact CTA match
    contact_match = None
    for pat in CONTACT_CTA_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            contact_match = (m.group(0), m.start(), m.end())
            break

    # Family emergency match
    family_match = None
    for pat in FAMILY_EMERGENCY_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            family_match = (m.group(0), m.start(), m.end())
            break

    has_scam_context = False

    # -------------------------------------------------------------
    # COMBINATION RULES
    # -------------------------------------------------------------

    # A. ACCOUNT_THREAT = ASSET + THREAT
    if asset_match and threat_match:
        has_scam_context = True
        ev_asset = extract_evidence_snippet(original_text, asset_match[1], asset_match[2])
        ev_threat = extract_evidence_snippet(original_text, threat_match[1], threat_match[2])
        indicators.append(
            Indicator(
                code="ACCOUNT_THREAT",
                label="Account, service, or asset suspension threat",
                severity="high",
                weight=0.55,
                evidence=f"{ev_asset} + {ev_threat}",
            )
        )

    # B. REWARD_LURE = REWARD + (AMOUNT or FEE_DEMAND or CONTACT_CTA)
    if reward_match and (amount_match or fee_match or contact_match or "lottery" in search_text or "prize" in search_text or "cashback" in search_text):
        has_scam_context = True
        ev_reward = extract_evidence_snippet(original_text, reward_match[1], reward_match[2])
        is_active_lure = bool(fee_match or contact_match or "lottery" in search_text or "prize" in search_text or "claim" in search_text or "won" in search_text)
        weight = 0.50 if is_active_lure else 0.35
        severity = "high" if is_active_lure else "low"
        indicators.append(
            Indicator(
                code="REWARD_LURE",
                label="Unsolicited reward, lottery, or prize lure",
                severity=severity,
                weight=weight,
                evidence=ev_reward,
            )
        )

    # C. ADVANCE_FEE = FEE_DEMAND + (REWARD or THREAT or AUTHORITY or INVESTMENT_JOB or AMOUNT)
    if fee_match and (reward_match or threat_match or auth_match or inv_match or amount_match):
        has_scam_context = True
        ev_fee = extract_evidence_snippet(original_text, fee_match[1], fee_match[2])
        indicators.append(
            Indicator(
                code="ADVANCE_FEE",
                label="Advance fee, GST, or upfront processing deposit demand",
                severity="high",
                weight=0.60,
                evidence=ev_fee,
            )
        )

    # D. CREDENTIAL_PHISH = CREDENTIAL_REQUEST (High severity; anti-gaming applies)
    if cred_match:
        has_scam_context = True
        ev_cred = extract_evidence_snippet(original_text, cred_match[1], cred_match[2])
        indicators.append(
            Indicator(
                code="CREDENTIAL_PHISH",
                label="Solicitation of confidential credential, PIN, OTP, or identity document",
                severity="high",
                weight=0.65,
                evidence=ev_cred,
            )
        )

    # E. AUTHORITY_INTIMIDATION = AUTHORITY + THREAT
    if auth_match and threat_match:
        has_scam_context = True
        ev_auth = extract_evidence_snippet(original_text, auth_match[1], auth_match[2])
        ev_threat = extract_evidence_snippet(original_text, threat_match[1], threat_match[2])
        indicators.append(
            Indicator(
                code="AUTHORITY_INTIMIDATION",
                label="Government or law enforcement intimidation threat",
                severity="high",
                weight=0.65,
                evidence=f"{ev_auth} + {ev_threat}",
            )
        )

    # F. UNSOLICITED_CONTACT = CONTACT_CTA + (THREAT or REWARD or FEE_DEMAND or ASSET)
    if contact_match and (threat_match or reward_match or fee_match or asset_match):
        has_scam_context = True
        ev_contact = extract_evidence_snippet(original_text, contact_match[1], contact_match[2])
        indicators.append(
            Indicator(
                code="UNSOLICITED_CONTACT",
                label="Unsolicited coercive call, message, or link redirect",
                severity="medium",
                weight=0.40,
                evidence=ev_contact,
            )
        )

    # G. INVESTMENT_JOB_FRAUD = INVESTMENT_JOB
    if inv_match:
        has_scam_context = True
        ev_inv = extract_evidence_snippet(original_text, inv_match[1], inv_match[2])
        severity = "high" if (fee_match or "guaranteed" in search_text or "vip" in search_text) else "medium"
        weight = 0.60 if severity == "high" else 0.50
        indicators.append(
            Indicator(
                code="INVESTMENT_JOB_FRAUD",
                label="Unrealistic investment return or task-based job scheme",
                severity=severity,
                weight=weight,
                evidence=ev_inv,
            )
        )

    # H. FAMILY_EMERGENCY_IMPERSONATION
    if family_match:
        has_scam_context = True
        ev_family = extract_evidence_snippet(original_text, family_match[1], family_match[2])
        indicators.append(
            Indicator(
                code="FAMILY_EMERGENCY_IMPERSONATION",
                label="Urgent family impersonation requesting immediate fund transfer",
                severity="high",
                weight=0.60,
                evidence=ev_family,
            )
        )

    # I. URGENCY_PRESSURE: Fires only if accompanying a scam context/lure
    if urgency_match and has_scam_context:
        ev_urg = extract_evidence_snippet(original_text, urgency_match[1], urgency_match[2])
        indicators.append(
            Indicator(
                code="URGENCY_PRESSURE",
                label="Coercive psychological urgency pressuring immediate action",
                severity="medium",
                weight=0.35,
                evidence=ev_urg,
            )
        )

    return indicators
