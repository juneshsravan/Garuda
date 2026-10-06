import re
from typing import List, Dict, Any, Optional

class Indicator:
    def __init__(self, code: str, label: str, severity: str, weight: float, evidence: Optional[str] = None):
        self.code = code
        self.label = label
        self.severity = severity  # "low" | "medium" | "high" | "critical"
        self.weight = weight
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "severity": self.severity,
            "weight": self.weight,
            "evidence": self.evidence,
        }


def extract_evidence_snippet(text: str, match_start: int, match_end: int, window: int = 20) -> str:
    """Extracts evidence cut cleanly on word boundaries around the match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)

    # Align start to word boundary
    if start > 0:
        prev_space = text.rfind(" ", 0, match_start)
        if prev_space != -1 and prev_space >= start - 15:
            start = prev_space + 1

    # Align end to word boundary
    if end < len(text):
        next_space = text.find(" ", match_end)
        if next_space != -1 and next_space <= end + 15:
            end = next_space

    return text[start:end].strip()


RULES = [
    # 1. Credential & Security Solicitations (High)
    # Notice: Negative context check ensures safety advisories ("Do not share OTP") NEVER trigger OTP theft rules!
    {
        "code": "CRED_OTP_REQUEST",
        "label": "Direct request to share or provide confidential OTP",
        "severity": "high",
        "weight": 0.55,
        "patterns": [
            r"\b(?:share|send|provide|tell)\s+(?:your\s+)?otp\b",
            r"\bsh[a@]re\s+y[o0]ur\s+[o0]tp\b",
            r"\botp\s+(?:saajha|saajhaa|bhejo|batao|share)\s+(?:karein|karo|kijiye)\b",
            r"अपना\s+otp\s+साझा\s+करें",
            r"మీ\s+otp\s+చెప్పండి",
        ],
        "check_negation": True,
    },
    {
        "code": "CRED_PIN_REQUEST",
        "label": "Deceptive prompt to enter UPI PIN to receive money",
        "severity": "high",
        "weight": 0.60,
        "patterns": [
            r"\benter\s+(?:your\s+)?(?:upi\s+)?pin\s+to\s+receive\b",
            r"\bmee\s+upi\s+pin\s+enter\s+cheyandi\b",
            r"\bpin\s+enter\s+karein\s+paise\s+paane\b",
            r"\benter\s+(?:your\s+)?pin\s+to\s+receive\s+it\b",
        ],
    },
    {
        "code": "UPI_COLLECT_REQUEST_TRAP",
        "label": "Deceptive prompt to approve an incoming collect request to receive funds",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bapprove\s+(?:the\s+)?request\s+on\s+your\s+upi\s+app\b",
            r"\bapprove\s+(?:the\s+)?request\s+.*enter\s+(?:your\s+)?pin\b",
        ],
    },
    {
        "code": "CRED_CARD_DETAILS_PROMPT",
        "label": "Request to re-enter sensitive payment card or banking details",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bre-?enter\s+your\s+card\s+details\b",
            r"\bsubmit\s+your\s+bank\s+details\b",
            r"\benter\s+card\s+details\b",
        ],
    },

    # 2. Account Suspension & Utility Disconnection Threats (High)
    {
        "code": "ACC_SUSPENSION_THREAT",
        "label": "Threat of immediate account suspension or service termination",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\b(?:account|yono|sim|card)\s+will\s+be\s+(?:suspended|blocked|deactivated|closed)\b",
            r"\bsim\s+card\s+\d+\s+ghante\s+me\s+band\s+ho\s+jayega\b",
            r"बैंक\s+खाता\s+आज\s+बंद\s+हो\s+जाएगा",
            r"బ్యాంక్\s+ఖాతా\s+ఈరోజు\s+బ్లాక్\s+అవుతుంది",
            r"\bav[o0]id\s+acc[o0]unt\s+bl[o0]ck\b",
        ],
    },
    {
        "code": "UTIL_DISCONNECT_THREAT",
        "label": "Threat of power or utility service disconnection",
        "severity": "high",
        "weight": 0.55,
        "patterns": [
            r"\b(?:electricity|power)\s+(?:power\s+)?will\s+be\s+disconnected\b",
            r"\bprevious\s+month\s+bill\s+was\s+not\s+updated\b",
        ],
    },
    {
        "code": "KYC_COERCION",
        "label": "Urgent mandate to update PAN or KYC under penalty of block",
        "severity": "high",
        "weight": 0.45,
        "patterns": [
            r"\bupdate\s+pan\s+(?:immediately|today|now)\b",
            r"\bkyc\s+update\s+ke\s+liye\s+turant\b",
            r"kyc\s+అప్‌డేట్\s+కోసం\s+వెంటనే",
            r"kyc\s+अपडेट\s+करने\s+के\s+लिए\s+तुरंत",
            r"\bkyc\s+update\s+(?:immediately|turant)\b",
        ],
    },
    {
        "code": "UNOFFICIAL_OFFICER_CTA",
        "label": "Directing critical dispute resolution to personal mobile officer number",
        "severity": "medium",
        "weight": 0.40,
        "patterns": [
            r"\bcall\s+our\s+officer\s+[6-9]\d{9}\b",
            r"\bcall\s+our\s+officer\b",
            r"\bturant\s+is\s+number\s+pe\s+call\s+karo\b",
        ],
    },

    # 3. QR Code & Deceptive Reward Actions (High)
    {
        "code": "QR_PAY_REWARD_TRAP",
        "label": "Fraudulent instruction to scan QR code to claim reward",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bscan\s+this\s+qr\s+(?:immediately\s+)?to\s+claim\b",
            r"\bscan\s+qr\s+to\s+(?:receive|claim|get)\b",
        ],
    },

    # 4. Job, Task & Investment Fraud (High)
    {
        "code": "JOB_TASK_FRAUD",
        "label": "Unrealistic part-time task fraud with upfront payment demand",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\blike\s+youtube\s+videos\s+and\s+earn\b",
            r"\bpart\s+time\s+job!.*earn\s+[₹$]?\d+\s+daily\b",
            r"\bcomplete\s+\d+\s+tasks\s+and\s+get\b",
            r"\bcontact\s+hr\s+on\s+telegram\b",
        ],
    },
    {
        "code": "TASK_DEPOSIT_DEMAND",
        "label": "Requirement to deposit funds to unlock VIP tasks or earn returns",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bto\s+unlock\s+vip\s+tasks\s+deposit\b",
            r"\bdeposit\s+[₹$]?[\d,]+.*(?:guaranteed|returns)\b",
        ],
    },
    {
        "code": "FIN_INVESTMENT_GUARANTEE",
        "label": "Guaranteed abnormal financial returns or unregistered VIP stock tip scheme",
        "severity": "high",
        "weight": 0.65,
        "patterns": [
            r"\bguaranteed\s+\d+%\s+returns\b",
            r"\bvip\s+stock\s+tips\s+group\b",
            r"\bsebi-registered\s+vip\b",
        ],
    },
    {
        "code": "FIN_INSTANT_LOAN_UPFRONT",
        "label": "Advance-fee loan scam offering immediate disbursement without CIBIL",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\binstant\s+loan\s+.*approved\s+without\s+cibil\b",
            r"\bwithout\s+cibil\s+check\b",
        ],
    },
    {
        "code": "FIN_ADVANCE_FEE_DEMAND",
        "label": "Demand for upfront processing fee, GST or deposit to release funds",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bpay\s+[₹$]?[\d,]+\s+(?:processing\s+fee|charges|gst|deposit)\b",
            r"\bprocessing\s+fee\s+to\s+receive\b",
            r"\bpay\s+[₹$]?[\d,]+\s+gst\s+to\s+release\b",
        ],
    },

    # 5. Lottery & Government Impersonation (High)
    {
        "code": "FIN_LOTTERY_ADVANCE_FEE",
        "label": "Lottery prize advance-fee tax/GST release fraud",
        "severity": "high",
        "weight": 0.55,
        "patterns": [
            r"\bkbc\s+lucky\s+draw\s+winner\b",
            r"बधाई\s+हो!.*इनाम\s+जीता\s+है",
        ],
    },
    {
        "code": "FIN_CLICK_LINK_REWARD_CTA",
        "label": "Coercive link CTA promising monetary rewards or cashback",
        "severity": "high",
        "weight": 0.45,
        "patterns": [
            r"इनाम\s+पाने\s+के\s+लिए\s+अभी\s+इस\s+लिंक\s+पर\s+क्लिक\s+करें",
            r"\bee\s+link\s+click\s+chesi\b",
            r"\bclick\s+(?:this\s+)?link\s+to\s+(?:claim|receive|get)\b",
        ],
    },
    {
        "code": "GOV_IMPERSONATION_DIGITAL_ARREST",
        "label": "Law enforcement impersonation parcel threat (Digital Arrest)",
        "severity": "high",
        "weight": 0.65,
        "patterns": [
            r"\b(?:mumbai\s+customs|cbi|police|customs\s+department)\b.*(?:illegal\s+drugs|narcotics|arrest)\b",
            r"\bjoin\s+a\s+video\s+call\s+with\s+a\s+(?:cbi|police)\s+officer\b",
            r"\bface\s+immediate\s+arrest\b",
        ],
    },
    {
        "code": "FIN_TAX_REFUND_PHISH",
        "label": "Tax authority refund bait with unverified submission link",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bincome\s+tax\s+dept:.*eligible\s+for\s+a\s+refund\b",
            r"\bsubmit\s+your\s+bank\s+details\s+at\b",
        ],
    },
    {
        "code": "UPI_ACCIDENTAL_TRANSFER_BAIT",
        "label": "False claim of accidental fund transfer to trick victim into approving collect request",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bi\s+sent\s+[₹$]?[\d,]+\s+to\s+you\s+by\s+mistake\b",
            r"\bgalti\s+se\s+(?:paise|amount)\b",
        ],
    },
    {
        "code": "FAMILY_EMERGENCY_IMPERSONATION",
        "label": "Urgent family emergency impersonation requesting money transfer",
        "severity": "high",
        "weight": 0.55,
        "patterns": [
            r"\bhi\s+mom,\s+this\s+is\s+my\s+new\s+number\b",
            r"\bmy\s+phone\s+broke\b",
        ],
    },
    {
        "code": "FIN_DIRECT_PAYMENT_DEMAND",
        "label": "Direct demand to transfer money urgently to personal handle or number",
        "severity": "high",
        "weight": 0.50,
        "patterns": [
            r"\bplease\s+send\s+[₹$]?[\d,]+\s+urgently\b",
            r"\bsend\s+[₹$]?[\d,]+\s+urgently\s+to\b",
        ],
    },

    # 6. Unsolicited Monetary Rewards & Prizes (High)
    {
        "code": "FIN_UNEXPECTED_REWARD",
        "label": "Unsolicited monetary reward or prize claim bait",
        "severity": "high",
        "weight": 0.45,
        "patterns": [
            r"\bcongratulations!?\s+you\s+won\s+[₹$]?[\d,]+\b",
            r"\bmeeku\s+[₹$]?[\d,]+\s+cashback\s+vachindi\b",
            r"\byou\s+won\s+[₹$]?[\d,]+\s+(?:lakh|crore|prize)\b",
            r"आपने\s+[₹$]?[\d,]+\s+का\s+इनाम\s+जीता\s+है",
            r"\bclaim\s+(?:your\s+)?reward\b",
        ],
    },

    # 7. Coercive Urgency & Pressure (Medium)
    {
        "code": "URGENCY_PRESSURE",
        "label": "Coercive urgency pressuring immediate action",
        "severity": "medium",
        "weight": 0.30,
        "patterns": [
            r"\b(?:immediately|urgently)\b",
            r"\btonight\s+at\s+\d+:\d+\s*(?:pm|am)?\b",
            r"\bwithin\s+24\s+hours\b",
            r"\b2\s+ghante\s+me\b",
            r"\blimited\s+seats\b",
            r"\bअभी\b",
            r"\bventane\b",
            r"\bturant\b",
            r"\bn0w\b",
        ],
    },
]


NEGATION_WORDS = ["do not", "don't", "dont", "never", "not", "mat", "na", "వద్దు", "లేదు", "नहीं", "मत"]


def is_negated_match(text: str, match_start: int) -> bool:
    """Checks if the matched phrase is immediately preceded by an authentic safety warning/negation."""
    prefix_window = text[max(0, match_start - 35):match_start].lower()
    return any(neg in prefix_window for neg in NEGATION_WORDS)


def analyze_text_rules(search_text: str, original_text: str) -> List[Indicator]:
    """
    Evaluates context-aware threat detection rules against normalized search text.
    Extracts evidence snippets from original text on word boundaries.
    """
    detected: List[Indicator] = []

    for rule in RULES:
        matched = False
        for pat in rule["patterns"]:
            m = re.search(pat, search_text, re.IGNORECASE)
            if m:
                if rule.get("check_negation") and is_negated_match(search_text, m.start()):
                    continue
                evidence = extract_evidence_snippet(original_text, m.start(), m.end())
                detected.append(
                    Indicator(
                        code=rule["code"],
                        label=rule["label"],
                        severity=rule["severity"],
                        weight=rule["weight"],
                        evidence=evidence,
                    )
                )
                matched = True
                break
        if matched:
            continue

    return detected
