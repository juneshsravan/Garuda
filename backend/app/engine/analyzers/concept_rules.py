import re
import os
from typing import List, Dict, Any, Optional, Tuple
import yaml

from app.engine.analyzers.text_rules import Indicator, extract_evidence_snippet

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


def get_concept_terms(concepts: Dict[str, Any], concept_name: str) -> List[str]:
    """Retrieves all terms across all supported languages for a given concept."""
    c = concepts.get(concept_name, {})
    if isinstance(c, dict):
        terms: List[str] = []
        for lang_terms in c.values():
            if isinstance(lang_terms, list):
                terms.extend(lang_terms)
        return terms
    elif isinstance(c, list):
        return c
    return []


ENGLISH_WORDS = {
    "account", "bank", "wallet", "card", "credit", "debit", "limit", "loan", "policy", "insurance", "emi",
    "block", "blocked", "blocking", "suspend", "suspended", "suspension", "deactivate", "deactivated",
    "expire", "expired", "disconnect", "disconnected", "disconnection", "close", "closed", "freeze", "frozen",
    "today", "tonight", "now", "immediately", "urgent", "urgently", "chance", "seats", "hours",
    "won", "winner", "prize", "reward", "lottery", "lucky", "cashback", "refund", "bonus", "gift", "congrats", "congratulations", "selected",
    "customs", "police", "court", "officer", "board", "cell",
    "fee", "fees", "charges", "charge", "gst", "tax", "deposit", "payment",
    "earn", "earning", "daily", "week", "task", "tasks", "returns",
    "hotel", "hotels", "rating", "review", "video", "videos", "subscribe", "follow",
    "mom", "dad", "brother", "sister", "friend", "number", "phone", "broken", "lost",
    "send", "transfer", "receive",
    "otp", "pin", "pan", "sim", "aadhaar", "kyc", "upi", "cvv", "sms", "cbi", "rbi", "trai",
    "click", "open", "call", "whatsapp", "telegram", "link", "visit", "redeem", "contact",
    "share", "enter", "provide", "submit", "update", "verify",
}


def is_damerau_levenshtein_1(s1: str, s2: str) -> bool:
    """Checks if s1 and s2 have Damerau-Levenshtein edit distance <= 1 (with transpositions)."""
    if s1 == s2:
        return True
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > 1:
        return False
    if len1 == len2:
        diffs = [i for i in range(len1) if s1[i] != s2[i]]
        if len(diffs) == 1:
            return True
        if len(diffs) == 2:
            i, j = diffs
            if j == i + 1 and s1[i] == s2[j] and s1[j] == s2[i]:
                return True
        return False
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    i = 0
    while i < len1 and s1[i] == s2[i]:
        i += 1
    return s1[i:] == s2[i+1:]


def is_indic_text(text: str) -> bool:
    """Checks whether the text contains characters from supported Indic Unicode ranges."""
    return any(
        "\u0900" <= c <= "\u097f" or  # Devanagari
        "\u0c00" <= c <= "\u0c7f" or  # Telugu
        "\u0c80" <= c <= "\u0cff" or  # Kannada
        "\u0b80" <= c <= "\u0bff" or  # Tamil
        "\u0d00" <= c <= "\u0d7f"     # Malayalam
        for c in text
    )


def find_lexicon_match(terms: List[str], text: str) -> Optional[Tuple[str, int, int]]:
    """
    Searches for terms in text matching on word boundaries.
    Applies exact matching first across all languages.
    If no exact match, applies fuzzy matching for romanized words only:
    - Words of 5+ letters match a lexicon word within edit distance 1 (with transpositions).
    - Never fuzzy-matches short words (<5 letters) or English words like OTP/PIN.
    """
    # 1. Exact match across all languages (code-mixing)
    for term in terms:
        if is_indic_text(term):
            idx = text.find(term.lower())
            if idx != -1:
                return term, idx, idx + len(term)
        else:
            pat = r"\b" + re.escape(term) + r"\b"
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return term, m.start(), m.end()

    # 2. Fuzzy match for romanized words only (length >= 5, not English)
    text_words = list(re.finditer(r"\b[a-zA-Z]{5,}\b", text))
    if text_words:
        for term in terms:
            if is_indic_text(term):
                continue
            term_clean = term.strip().lower()
            term_parts = term_clean.split()
            if len(term_parts) == 1:
                lex_word = term_parts[0]
                if len(lex_word) >= 5 and lex_word not in ENGLISH_WORDS and lex_word.isalpha():
                    for tw in text_words:
                        w = tw.group(0).lower()
                        if w not in ENGLISH_WORDS and is_damerau_levenshtein_1(w, lex_word):
                            return term, tw.start(), tw.end()

    return None


NEGATION_WORDS = [
    # English
    "do not", "don't", "dont", "never", "not", "mat", "na",
    # Hindi / Hinglish
    "kisi ko nahi", "kisi ko mat", "नहीं", "मत", "ना", "साझा न करें",
    # Telugu
    "వద్దు", "లేదు", "చెప్పకండి",
    # Kannada
    "ಬೇಡಿ", "ಹಂಚಿಕೊಳ್ಳಬೇಡಿ", "ಮಾಡಬೇಡಿ", "ಇಲ್ಲ", "bedi", "hanchikollabedi", "madabedi",
    # Tamil
    "வேண்டாம்", "பகிராதீர்கள்", "செய்யாதீர்கள்", "இல்லை", "vendam", "pagiradheergal", "seiyatheergal",
    # Malayalam
    "അരുത്", "പങ്കിടരുത്", "ചെയ്യരുത്", "ഇല്ല", "aruthu", "pankidaruthu", "cheyyaruthu",
]


def is_negated_phrase(text: str, start: int) -> bool:
    """Checks if the phrase is preceded by an authentic warning or negative qualifier."""
    prefix = text[max(0, start - 35):start].lower()
    return any(neg in prefix for neg in NEGATION_WORDS)


# Protective advice check (e.g., "Not you? Block it in the app")
PROTECTIVE_ADVICE_PATTERNS = [
    r"\bnot\s+you\??\s+(?:block\s+it|report\s+it)\b",
    r"\bblock\s+(?:it|your\s+card|your\s+account)\s+in\s+the\s+[a-z0-9_-]+\s+app\b",
    r"\bcall\s+the\s+number\s+on\s+the\s+back\s+of\s+your\s+card\b",
    r"\breport\s+it\s+(?:via|in|through)\s+(?:the\s+)?(?:official\s+app|app)\b",
    r"\bif\s+not\s+you,\s+call\b",
]


AMOUNT_REGEX = re.compile(
    r"(?:[₹$€£]|rs\.?|inr)\s*[\d,]+(?:\.\d+)?|\b\d+\s*(?:lakh|crore|thousand|bonus)\b|"
    r"\b(?:charges|charge|fee|fees|bonus|credit|refund|loan|pay|send|bhejo|pampandi|kattandi|daalo|deposit|earning|earn|cashback|prize|reward|minimum|kattiri|pavathisi|seluthungal|kattungal|adakkuka|nalkuka)\s+(?:of\s+)?(\d{3,}(?:,\d{3})*)\b|"
    r"\b(\d{3,}(?:,\d{3})*)\s+(?:charges|charge|fee|fees|bonus|credit|refund|loan|bhejo|pampandi|kattandi|deposit|cashback|per\s+week|per\s+day|daily|kattiri|pavathisi|seluthungal|adakkuka)\b|"
    r"(?:ఫీజు|ఛార్జీలు|బోనస్|క్రెడిట్|రిఫండ్|లోన్|పంపండి|కట్టండి|డిపాజిట్)\s*(\d{3,}(?:,\d{3})*)|"
    r"(\d{3,}(?:,\d{3})*)\s*(?:ఫీజు|ఛార్జీలు|బోనస్|క్రెడిట్|రిఫండ్|లోన్|పంపండి|కట్టండి|డిపాజిట్)|"
    r"(?:फीस|चार्ज|शुल्क|बोनस|क्रेडिट|रिफंड|लोन|भेजें|भेजो|जमा|डिपॉजिट)\s*(\d{3,}(?:,\d{3})*)|"
    r"(\d{3,}(?:,\d{3})*)\s*(?:फीस|चार्ज|शुल्क|बोनस|क्रेडिट|रिफंड|लोन|भेजें|भेजो|जमा|डिपॉजिट)|"
    r"(?:ಶುಲ್ಕ|ಠೇವಣಿ|ಸಾಲ|ಗಳಿಸಿ|ಬಹುಮಾನ|ಕಟ್ಟಿ|ಪಾವತಿಸಿ|ಕಳುಹಿಸಿ)\s*(\d{3,}(?:,\d{3})*)|"
    r"(\d{3,}(?:,\d{3})*)\s*(?:ಶುಲ್ಕ|ಠೇವಣಿ|ಸಾಲ|ಗಳಿಸಿ|ಬಹುಮಾನ|ಕಟ್ಟಿ|ಪಾವತಿಸಿ|ಕಳುಹಿಸಿ)|"
    r"(?:கட்டணம்|வைப்புத்தொகை|கடன்|பரிசு|செலுத்துங்கள்|கட்டுங்கள்|அனுப்புங்கள்)\s*(\d{3,}(?:,\d{3})*)|"
    r"(\d{3,}(?:,\d{3})*)\s*(?:கட்டணம்|வைப்புத்தொகை|கடன்|பரிசு|செலுத்துங்கள்|கட்டுங்கள்|அனுப்புங்கள்)|"
    r"(?:ഫീസ്|നിക്ഷേപം|വായ്പ|സമ്മാനം|അടയ്ക്കുക|നൽകുക|അയക്കുക)\s*(\d{3,}(?:,\d{3})*)|"
    r"(\d{3,}(?:,\d{3})*)\s*(?:ഫീസ്|നിക്ഷേപം|വായ്പ|സമ്മാനം|അടയ്ക്കുക|നൽകുക|അയക്കുക)",
    re.IGNORECASE
)

FEE_DEMAND_PATTERNS = [
    r"\b(?:pay|deposit|send|bharo|kattandi|pampu|pampandi|pampinchandi|transfer|jama\s+karo|kattiri|pavathisi|seluthungal|kattungal|adakkuka|nalkuka)\s+.*?(?:fee|fees|charges|charge|amount|deposit|processing|gst|tax|registration|redelivery|release|shulka|thevani|kattanam|nikshepam)\b",
    r"\b(?:fee|fees|charges|charge|tax|gst|deposit|amount|payment|shulka|thevani|kattanam|nikshepam)\s+(?:bharo|kattandi|pampandi|do|pay|bhar|jama\s+karo|kattu|pampu|kattiri|pavathisi|seluthungal|kattungal|adakkuka|nalkuka)\b",
    r"\b(?:joining|registration|processing|security|activation|membership|delivery)\s+(?:fee|fees|charges|charge|amount|deposit|payment|shulka|kattanam)\s+(?:of\s+)?(?:rs\.?|inr|[₹$])?\s*[\d,]+\b",
    r"\b(?:rs\.?|inr|[₹$])?\s*[\d,]+\s+(?:joining|registration|processing|security|activation|delivery)\s+(?:fee|fees|charges|charge|amount|deposit|payment|shulka|kattanam)\b",
    r"\b(?:joining|registration|processing|security|activation|delivery)\s+(?:fee|fees|charges|charge|amount|deposit|payment|shulka|kattanam)\s+[\d,]+\b",
    r"\b(?:fee|fees|charges|charge|deposit|amount|payment|shulka|kattanam)\s+(?:of\s+)?[₹$]?[\d,]+\b",
    r"\bto\s+unlock\s+vip\s+tasks\s+deposit\b",
    r"\b(?:processing|registration|delivery)\s+(?:fee|fees|charges|charge|amount|deposit|payment|shulka|kattanam)\b",
    # Telugu
    r"(?:ప్రాసెసింగ్|రిజిస్ట్రేషన్|డెలివరీ)\s+(?:ఫీజు|ఛార్జీలు|రుసుము|మొత్తం|డిపాజిట్|చెల్లింపు)",
    r"(?:ఫీజు|ఛార్జీలు|రుసుము|మొత్తం|డిపాజిట్)\s*.*?(?:చెల్లించండి|కట్టండి|పంపండి|చేయండి)",
    r"(?:ఫీజు|ఛార్జీలు|రుసుము|డిపాజిట్)\s*[\d,]+",
    # Hindi
    r"(?:प्रोसेसिंग|रजिस्ट्रेशन|डिलीवरी)\s+(?:फीस|चार्ज|शुल्क|रकम|डिपॉजिट|भुगतान)",
    r"(?:फीस|चार्ज|शुल्क|रकम|डिपॉजिट)\s*.*?(?:भरो|जमा\s+करें|भेजें|दीजिए|पे\s+करें)",
    r"(?:फीस|चार्ज|शुल्क|डिपॉजिट)\s*[\d,]+",
    # Kannada
    r"(?:ಪ್ರೊಸೆಸಿಂಗ್|ನೋಂದಣಿ|ಡೆಲಿವರಿ)\s+(?:ಶುಲ್ಕ|ಠೇವಣಿ|ಹಣ)",
    r"(?:ಶುಲ್ಕ|ಠೇವಣಿ|ತೆರಿಗೆ)\s*.*?(?:ಪಾವತಿಸಿ|ಕಟ್ಟಿ|ಕಳುಹಿಸಿ|ಮಾಡಿ)",
    r"(?:ಶುಲ್ಕ|ಠೇವಣಿ)\s*[\d,]+",
    # Tamil
    r"(?:செயலாக்க|பதிவு|டெலிவரி)\s+(?:கட்டணம்|வைப்புத்தொகை)",
    r"(?:கட்டணம்|வைப்புத்தொகை|வரி)\s*.*?(?:செலுத்துங்கள்|கட்டுங்கள்|அனுப்புங்கள்)",
    r"(?:கட்டணம்|வைப்புத்தொகை)\s*[\d,]+",
    # Malayalam
    r"(?:പ്രോസസ്സിംഗ്|രജിസ്ട്രേഷൻ|ഡെലിവറി)\s+(?:ഫീസ്|നിക്ഷേപം)",
    r"(?:ഫീസ്|നിക്ഷേപം|നികുതി)\s*.*?(?:അടയ്ക്കുക|നൽകുക|അയക്കുക)",
    r"(?:ഫീസ്|നിക്ഷേപം)\s*[\d,]+",
]

CREDENTIAL_REQUEST_PATTERNS = [
    r"\b(?:share|send|tell|enter|cheppandi|bhejo|saajha|batao|provide|submit|re-?enter|daalo|dalo|enter\s+karo|ivvandi|type\s+karo|hanchikolli|namoodisi|pagiravum|ullidavum|pankiduka|nalkuka)\s+.*?(?:otp|pin|password|cvv|card\s+details|bank\s+details|aadhaar|pan)\b",
    r"\botp\s+(?:daalo|dalo|enter\s+karo|batao|bhejo|ivvandi|cheppandi|enter\s+cheyandi|type\s+karo|hanchikolli|namoodisi|pagiravum|ullidavum|pankiduka|nalkuka|share\s+maadi|share\s+seiyavum|share\s+cheyyuka)\b",
    r"\b(?:daalo|dalo|enter\s+karo|ivvandi|type\s+karo)\s+otp\b",
    r"\bsh[a@]re\s+y[o0]ur\s+[o0]tp\b",
    r"\bmee\s+upi\s+pin\s+enter\s+cheyandi\b",
    r"\bअपना\s+otp\s+साझा\s+करें\b",
    r"अपना\s+otp\s+(?:साझा\s+करें|डालो|दर्ज\s+करें|बताओ|भेजें)",
    r"otp\s+(?:डालो|दर्ज\s+करें|बताओ)",
    r"మీ\s+(?:otp|పిన్)\s+(?:చెప్పండి|నమోదు\s+చేయండి|ఇవ్వండి|టైప్\s+చేయండి)",
    r"\bమీ\s+otp\s+చెప్పండి\b",
    # Kannada
    r"ನಿಮ್ಮ\s+(?:ಒಟಿಪಿ|ಪಿನ್|ಪಾಸ್‌ವರ್ಡ್)\s*(?:ಹಂಚಿಕೊಳ್ಳಿ|ನಮೂದಿಸಿ|ಕಳುಹಿಸಿ|ತಿಳಿಸಿ)",
    r"(?:ಒಟಿಪಿ|ಪಿನ್|ಪಾಸ್‌ವರ್ಡ್)\s*(?:ಹಂಚಿಕೊಳ್ಳಿ|ನಮೂದಿಸಿ|ಕಳುಹಿಸಿ|ಹಾಕಿ)",
    # Tamil
    r"உங்கள்\s+(?:ஓடிபி|பின்|கடவுச்சொல்)\s*(?:பகிரவும்|உள்ளிடவும்|அனுப்பவும்|கூறவும்)",
    r"(?:ஓடிபி|பின்|கடவுச்சொல்)\s*(?:பகிரவும்|உள்ளிடவும்|அனுப்பவும்)",
    # Malayalam
    r"നിങ്ങളുടെ\s+(?:ഒടിപി|പിൻ|പാസ്‌വേഡ്)\s*(?:പങ്കിടുക|നൽകുക|അയക്കുക|പറയുക)",
    r"(?:ഒടിപി|പിൻ|പാസ്‌വേഡ്)\s*(?:പങ്കിടുക|നൽകുക|അയക്കുക)",
    r"\bapprove\s+(?:the\s+)?request\s+on\s+your\s+upi\s+app\b",
    r"\benter\s+(?:your\s+)?pin\s+to\s+receive\b",
    r"\bsend\s+your\s+aadhaar\b",
    r"\bupdate\s+pan\s+immediately\b",
    r"\bkyc\s+update\s+ke\s+liye\b",
    r"\bkyc\s+ಅಪ್‌ಡೇಟ್\s+ಕೋಸಂ\b",
    r"\bkyc\s+अपडेट\s+करने\s+के\s+लिए\b",
    r"\bkyc\s+ನವೀಕರಣಕ್ಕಾಗಿ\b",
    r"\bkyc\s+புதுப்பிக்க\b",
    r"\bkyc\s+പുതുക്കാൻ\b",
]

CONTACT_CTA_PATTERNS = [
    r"\b(?:call|calling|whatsapp|contact)\s+(?:our\s+officer\s+|officer\s+|hr\s+|us\s+at\s+)?(?:\+?91[\s-]?)?[6-9]\d{9}\b",
    r"\bcontact\s+(?:hr\s+)?(?:on\s+)?(?:telegram|whatsapp|phone)\s+@?[a-z0-9_]+\b",
    r"\b(?:ye|is|ee|this|indha)\s+link\s+(?:open\s+karke|open\s+karo|pe\s+click\s+karo|par\s+click\s+karein|open\s+cheyandi|open\s+chesi|lo\s+update\s+cheyyandi|click\s+chesi|click\s+maadi|open\s+maadi|click\s+seiyavum|open\s+seiyavum|click\s+cheyyuka|open\s+cheyyuka)\b",
    r"\blink\s+(?:open\s+karke|open\s+karo|pe\s+click|par\s+click|open\s+cheyandi|open\s+chesi|click\s+maadi|open\s+maadi|click\s+seiyavum|open\s+seiyavum|click\s+cheyyuka|open\s+cheyyuka)\b",
    r"\b(?:click|open|visit)\s+(?:this\s+|here\s+|the\s+)?(?:link|url)\b",
    r"\bscan\s+(?:this\s+)?qr\b",
    r"\bredeem\s+now\b",
    r"\bcomplete\s+kyc\s+by\s+calling\b",
    r"\bcall\s+our\s+officer\b",
    r"\bturant\s+is\s+number\s+pe\s+call\b",
    r"(?:इस\s+)?(?:लिंक|link)\s*(?:पर|pe)?\s*(?:क्लिक\s*करें|क्लिक\s*करो|क्लिक|खोलें|ओपन)",
    r"(?:ఈ\s+)?(?:లింక్|link)\s*(?:పై|లో)?\s*(?:క్లిక్\s*చేయండి|క్లిక్|ఓపెన్\s*చేయండి|ఓపెన్)",
    r"(?:ಈ\s+)?(?:ಲಿಂಕ್|link)\s*(?:ಮೇಲೆ|ಅಲ್ಲಿ)?\s*(?:ಕ್ಲಿಕ್\s*ಮಾಡಿ|ತೆರೆಯಿರಿ|ಓಪನ್\s*ಮಾಡಿ)",
    r"(?:இந்த\s+)?(?:லிங்க்|link)\s*(?:ஐ|இல்)?\s*(?:கிளிக்\s*செய்யவும்|திறக்கவும்|ஓபன்\s*செய்யவும்)",
    r"(?:ഈ\s+)?(?:ലിങ്ക്|link)\s*(?:ൽ)?\s*(?:ക്ലിക്ക്\s*ചെയ്യുക|തുറക്കുക|ഓപ്പൺ\s*ചെയ്യുക)",
    r"इस\s+नंबर\s+पर\s+कॉल",
    r"नंबर\s+पर\s+कॉल\s+करें",
    r"\bee\s+link\s+(?:lo|click)\b",
    r"లింక్\s+ఓపెన్",
    r"లింక్\s+క్లిక్",
    r"ಲಿಂಕ್\s+ಕ್ಲಿಕ್\s*ಮಾಡಿ",
    r"ಲಿಂಕ್\s+ತೆರೆಯಿರಿ",
    r"லிங்கை\s*கிளிக்\s*செய்யவும்",
    r"லிங்க்\s*திறக்கவும்",
    r"ലിങ്കിൽ\s*ക്ലിക്ക്\s*ചെയ്യുക",
    r"ലിങ്ക്\s*തുറക്കുക",
    r"ಕರೆ\s*ಮಾಡಿ\s*[6-9]\d{9}",
    r"ಕರೆ\s*ಮಾಡಿ",
    r"ಸಂಪರ್ಕಿಸಿ",
    r"அழைக்கவும்\s*[6-9]\d{9}",
    r"அழைக்கவும்",
    r"தொடர்பு\s*கொள்ளவும்",
    r"വിളിക്കുക\s*[6-9]\d{9}",
    r"വിളിക്കുക",
    r"ബന്ധപ്പെടുക",
    r"వెంటనే\s+కాల్\s+చేయండి",
    r"కాల్\s+చేయండి\s*[6-9]\d{9}",
    r"కాల్\s+చేయండి",
]

EARNING_CLAIM_PATTERNS = [
    r"\b(?:earn|kamao|sampadinchandi|kamaye|earning|galisi|sampaadisi|sambaathikkavum|eettavum|sampaadhikkuka|neduka)\s+(?:rs\.?|inr|[₹$])?\s*[\d,]+(?:\s*[-/]\s*day|\s+per\s+day|\s+daily|\s+per\s+week|\s+per\s+task|\s+every\s+day|\s+ದಿನಕ್ಕೆ|\s+ಪ್ರತಿದಿನ|\s+தினமும்|\s+ஒரு\s+நாளைக்கு|\s+ദിവസവും|\s+പ്രതിദിനം)\b",
    r"\b(?:rs\.?|inr|[₹$])?\s*[\d,]+\s*[-/]\s*day\b",
]

TASK_ARCHETYPE_PATTERNS = [
    r"\b(?:rate|rating|review|like|subscribe|follow)\s+.*?(?:hotels|products|videos|pages|apps|places|youtube|google)\b",
]

MONEY_REQUEST_PATTERNS = [
    r"\b(?:send|bhej|bhejo|bhej\s+de|pampu|pampandi|transfer|daal\s+de|kaluhisi|vargayisi|anuppungal|ayakkuka)\s+.*?(?:rs\.?|inr|[₹$])?\s*[\d,]+.*?(?:gpay|phonepe|paytm|upi|ybl|account)?\b",
    r"\burgent(?:ly)?\s+(?:rs\.?|inr|[₹$])?\s*[\d,]+\s+(?:bhej|send|pampu|transfer|kaluhisi|anuppungal|ayakkuka)\b",
    r"\b(?:send|bhej|bhej\s+de|pampu|kaluhisi|anuppungal|ayakkuka)\s+(?:rs\.?|inr|[₹$])?\s*[\d,]+\b",
    r"\burgent\s+[\d,]+\s+bhej\s+de\b",
    r"\bhelp\.urgent@ybl\b",
]


def analyze_concept_combinations(search_text: str, original_text: str) -> List[Indicator]:
    """
    Evaluates order-independent combinations of conceptual signals per ARCHITECTURE Section 8.
    Produces high-fidelity indicators with concept-grounded evidence snippets.
    """
    concepts = load_concepts()
    indicators: List[Indicator] = []

    # 1. Match individual concepts from multilingual lexicons
    asset_match = find_lexicon_match(get_concept_terms(concepts, "ASSET"), search_text)
    threat_match = find_lexicon_match(get_concept_terms(concepts, "THREAT"), search_text)
    urgency_match = find_lexicon_match(get_concept_terms(concepts, "URGENCY"), search_text)
    reward_match = find_lexicon_match(get_concept_terms(concepts, "REWARD"), search_text)
    auth_match = find_lexicon_match(get_concept_terms(concepts, "AUTHORITY"), search_text)
    inv_match = find_lexicon_match(get_concept_terms(concepts, "EARNING_CLAIM"), search_text)
    relation_match = find_lexicon_match(get_concept_terms(concepts, "RELATION_OR_NEW_NUMBER"), search_text)

    # 2. Check protective-action context
    is_protective_threat = any(re.search(pat, search_text, re.IGNORECASE) for pat in PROTECTIVE_ADVICE_PATTERNS)

    # 3. Match regex-based concept actions
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

    # Earning claim match
    earning_match = None
    for pat in EARNING_CLAIM_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            earning_match = (m.group(0), m.start(), m.end())
            break

    # Task archetype match
    task_match = None
    for pat in TASK_ARCHETYPE_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            task_match = (m.group(0), m.start(), m.end())
            break

    # Money request match
    money_match = None
    for pat in MONEY_REQUEST_PATTERNS:
        m = re.search(pat, search_text, re.IGNORECASE)
        if m:
            money_match = (m.group(0), m.start(), m.end())
            break

    has_scam_context = False

    # -------------------------------------------------------------
    # COMBINATION RULES
    # -------------------------------------------------------------

    # A. ACCOUNT_THREAT = ASSET + THREAT (unless used as protective advice)
    if asset_match and threat_match and not is_protective_threat:
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
        is_active_lure = bool(fee_match or contact_match or "lottery" in search_text or "prize" in search_text or "claim" in search_text or "won" in search_text or "గెలుచుకున్నారు" in search_text)
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

    # C. ADVANCE_FEE = FEE_DEMAND + (REWARD or THREAT or AUTHORITY or INVESTMENT_JOB or AMOUNT or ASSET)
    if fee_match and (reward_match or threat_match or auth_match or inv_match or earning_match or amount_match or task_match or asset_match):
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

    # F. UNSOLICITED_CONTACT = CONTACT_CTA + (THREAT or REWARD or FEE_DEMAND or ASSET or EARNING_CLAIM or TASK_TYPE)
    if contact_match and (threat_match or reward_match or fee_match or asset_match or earning_match or task_match or inv_match):
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

    # G. INVESTMENT_JOB_FRAUD = (EARNING_CLAIM or TASK_TYPE or INVESTMENT_JOB) + (FEE_DEMAND or CONTACT_CTA or "from home")
    has_earning_signal = bool(inv_match or earning_match or task_match)
    has_job_context = bool(fee_match or contact_match or "from home" in search_text or "ghar baithe" in search_text or "deposit" in search_text or "returns" in search_text)
    if has_earning_signal and has_job_context:
        has_scam_context = True
        lead_match = earning_match or task_match or inv_match
        ev_inv = extract_evidence_snippet(original_text, lead_match[1], lead_match[2])
        severity = "high" if (fee_match or "guaranteed" in search_text or "vip" in search_text or "deposit" in search_text or "joining fee" in search_text) else "medium"
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

    # H. IMPERSONATION_MONEY_REQUEST = RELATION_OR_NEW_NUMBER + MONEY_REQUEST
    if relation_match and money_match:
        has_scam_context = True
        ev_rel = extract_evidence_snippet(original_text, relation_match[1], relation_match[2])
        ev_mon = extract_evidence_snippet(original_text, money_match[1], money_match[2])
        indicators.append(
            Indicator(
                code="IMPERSONATION_MONEY_REQUEST",
                label="Friend or family impersonation requesting urgent funds transfer",
                severity="high",
                weight=0.60,
                evidence=f"{ev_rel} + {ev_mon}",
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
