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
            r"\bnever\s+share\s+(?:your\s+)?(?:otp|pin|password)\b",
            r"\bdo\s+not\s+share\s+them\s+with\s+anyone\b",
        ],
    },
    {
        "code": "LEGIT_PROTECTIVE_ADVICE",
        "label": "Contains authentic user protective advisory or in-app defense step",
        "weight": 0.65,
        "patterns": [
            r"\bnot\s+you\??\s+(?:block\s+it|report\s+it)\b",
            r"\bblock\s+(?:it|your\s+card|your\s+account)\s+in\s+the\s+[a-z0-9_-]+\s+app\b",
            r"\bcall\s+the\s+number\s+on\s+the\s+back\s+of\s+your\s+card\b",
            r"\breport\s+it\s+(?:via|in|through)\s+(?:the\s+)?(?:official\s+app|app)\b",
            r"\bif\s+not\s+you,\s+call\b",
        ],
    },
    {
        "code": "LEGIT_MASKED_ACCOUNT",
        "label": "References masked account number or card ending",
        "weight": 0.50,
        "patterns": [
            r"\ba/?c\s+(?:xx|\*{2,})\d+\b",
            r"\baccount\s+(?:xx|\*{2,})\d+\b",
            r"\bcard\s+ending\s+(?:in\s+)?(?:\d{4}|xx\d{2,4})\b",
            r"\bending\s+(?:in\s+)?\d{4}\b",
            r"\bloan\s+a/?c\s+(?:xx|\*{2,})\d+\b",
        ],
    },
    {
        "code": "LEGIT_TRANSACTION_ALERT",
        "label": "Legitimate transaction debit/credit notification or service receipt",
        "weight": 0.55,
        "patterns": [
            r"\b(?:debited\s+from|credited\s+to)\s+(?:your\s+)?a/?c\b",
            r"\bavl\s+bal\s+(?:rs\.?|[₹$])?[\d,]+\b",
            r"\byour\s+emi\s+of\s+.*is\s+due\b",
            r"\bpaid\s+successfully\b",
            r"\breceipt\s+no\s+\d+\b",
            r"\bmaintain\s+sufficient\s+balance\b",
            r"\bwas\s+used\s+for\s+(?:rs\.?|[₹$])?[\d,]+\b",
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
            r"\b(?:order|parcel)\s+is\s+out\s+for\s+delivery\b",
            r"\byour\s+(?:flipkart|amazon|myntra|zomato|swiggy)\s+order\b",
            r"\btrack\s+it\s+in\s+the\s+[a-z]+\s+app\b",
            r"ऑर्डर\s+कल\s+डिलीवर\s+किया\s+जाएगा",
        ],
    },
    {
        "code": "LEGIT_OFFICIAL_CHANNEL_ADVICE",
        "label": "Directs actions strictly through verified official portal or app",
        "weight": 0.55,
        "patterns": [
            r"\bpay\s+through\s+the\s+official\s+(?:college\s+portal|website|app)\b",
            r"\bpay\s+via\s+the\s+official\s+(?:app|website)\b",
            r"\brecharge\s+via\s+the\s+(?:myjio|airtel|official)\s+app\b",
            r"\btrack\s+status\s+on\s+[a-z0-9.-]+\.gov\.in\b",
            r"\btrack\s+status\s+on\b",
        ],
    },
    {
        "code": "LEGIT_AUTOMATIC_WALLET_CREDIT",
        "label": "Automatic reward credited to internal wallet without PIN/QR action",
        "weight": 0.70,
        "patterns": [
            r"\bearned\s+[₹$]?\d+\s+cashback\s+on\s+your\s+recharge\b",
            r"\bhas\s+been\s+added\s+to\s+your\s+wallet\b",
        ],
    },
]


def analyze_legitimacy(
    search_text: str, original_text: str, urls: Optional[List[Dict[str, Any]]] = None
) -> List[LegitimacySignal]:
    """Evaluates legitimacy patterns that indicate safe, authentic communications."""
    detected: List[LegitimacySignal] = []

    # Check official domain presence
    if urls:
        for u in urls:
            if u.get("is_official"):
                detected.append(
                    LegitimacySignal(
                        code="LEGIT_OFFICIAL_DOMAIN",
                        label="Links directly to verified official government or corporate domain",
                        weight=0.55,
                        evidence=u.get("raw"),
                    )
                )
                break

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
