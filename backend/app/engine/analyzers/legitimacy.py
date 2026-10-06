import re
from typing import List, Dict, Any, Optional

from app.engine.analyzers.text_rules import extract_evidence_snippet

class LegitimacySignal:
    def __init__(self, code: str, label: str, weight: float, evidence: Optional[str] = None):
        self.code = code
        self.label = label
        self.weight = weight
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "weight": self.weight,
            "evidence": self.evidence,
        }


LEGITIMACY_RULES = [
    {
        "code": "LEGIT_BANK_NEVER_ASKS",
        "label": "Contains official bank anti-fraud safety advisory",
        "weight": 0.65,
        "patterns": [
            r"\bdo\s+not\s+share\s+otp\s+or\s+password\s+with\s+anyone\b",
            r"\bbank\s+never\s+calls\s+for\s+otp\b",
            r"\bsbi\s+never\s+asks\s+for\s+your\s+otp,\s+pin\s+or\s+password\b",
            r"\bnever\s+share\s+otp\b",
            r"\bdo\s+not\s+share\s+them\s+with\s+anyone\b",
        ],
    },
    {
        "code": "LEGIT_MASKED_ACCOUNT",
        "label": "References masked account number (e.g. A/c XX1234)",
        "weight": 0.50,
        "patterns": [
            r"\ba/?c\s+(?:xx|\*{2,})\d+\b",
            r"\baccount\s+xx\d+\b",
            r"\bcard\s+ending\s+(?:in\s+)?xx\d+\b",
        ],
    },
    {
        "code": "LEGIT_TRANSACTION_ALERT",
        "label": "Legitimate transaction debit/credit notification with official dispute advice",
        "weight": 0.55,
        "patterns": [
            r"\bdebited\s+from\s+a/?c\b.*(?:if\s+not\s+you,\s+call\s+the\s+number\s+on\s+the\s+back\s+of\s+your\s+card)\b",
            r"\bdebited\s+from\s+a/?c\b",
            r"\bcredited\s+to\s+a/?c\b",
            r"\bcall\s+the\s+number\s+on\s+the\s+back\s+of\s+your\s+card\b",
        ],
    },
    {
        "code": "LEGIT_STANDARD_OTP_ALERT",
        "label": "Standard transaction OTP format with timestamp expiry",
        "weight": 0.45,
        "patterns": [
            r"\byour\s+otp\s+for\s+transaction\s+of\s+.*valid\s+for\s+\d+\s+mins\b",
            r"\bvalid\s+for\s+\d+\s+mins\b",
        ],
    },
    {
        "code": "LEGIT_DELIVERY_NOTIFICATION",
        "label": "Standard e-commerce delivery status without coercive link",
        "weight": 0.50,
        "patterns": [
            r"\byour\s+(?:flipkart|amazon|myntra|zomato|swiggy)\s+order\s+.*will\s+be\s+delivered\b",
            r"\border\s+for\s+.*will\s+be\s+delivered\s+today\b",
        ],
    },
    {
        "code": "LEGIT_OFFICIAL_CHANNEL_ADVICE",
        "label": "Directs payment strictly through verified official portal or app",
        "weight": 0.55,
        "patterns": [
            r"\bpay\s+through\s+the\s+official\s+(?:college\s+portal|website|app)\b",
            r"\bpay\s+via\s+the\s+official\s+app\s+or\s+website\b",
        ],
    },
    {
        "code": "LEGIT_AUTOMATIC_WALLET_CREDIT",
        "label": "Automatic reward credited to internal wallet without PIN/QR action",
        "weight": 0.50,
        "patterns": [
            r"\bearned\s+[₹$]?\d+\s+cashback\s+on\s+your\s+recharge\b",
            r"\bhas\s+been\s+added\s+to\s+your\s+wallet\b",
        ],
    },
    {
        "code": "LEGIT_ACADEMIC_INFORMATIONAL",
        "label": "Routine educational or personal conversational inquiry",
        "weight": 0.40,
        "patterns": [
            r"\byou\s+were\s+absent\s+for\s+\d+(?:st|nd|rd|th)?\s+hour\b",
            r"\bthe\s+last\s+date\s+to\s+pay\s+semester\s+fees\b",
            r"\bsend\s+me\s+the\s+notes\s+from\s+yesterday's\s+lecture\b",
        ],
    },
]


def analyze_legitimacy(search_text: str, original_text: str) -> List[LegitimacySignal]:
    """Evaluates legitimacy patterns that indicate safe, authentic communications."""
    detected: List[LegitimacySignal] = []

    for rule in LEGITIMACY_RULES:
        matched = False
        for pat in rule["patterns"]:
            m = re.search(pat, search_text, re.IGNORECASE)
            if m:
                evidence = extract_evidence_snippet(original_text, m.start(), m.end())
                detected.append(
                    LegitimacySignal(
                        code=rule["code"],
                        label=rule["label"],
                        weight=rule["weight"],
                        evidence=evidence,
                    )
                )
                matched = True
                break
        if matched:
            continue

    return detected
