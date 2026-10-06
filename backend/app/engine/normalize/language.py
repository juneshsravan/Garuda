import re
from typing import Tuple

# Unicode range regexes
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")
TELUGU_SCRIPT_REGEX = re.compile(r"[\u0C00-\u0C7F]")

# Distinctive lexical markers for Romanized Indian languages
HINGLISH_MARKERS = {
    "aapka", "aapki", "aapko", "karo", "karein", "karna", "hoga", "jayega", "jayegi",
    "turant", "ghante", "paise", "khata", "band", "inaam", "jeet", "bhejo", "kijiye",
    "kripya", "galti", "se", "hai", "nahi", "ab", "aaj"
}

TELUGU_ROMAN_MARKERS = {
    "meeku", "vachindi", "cheyandi", "chesi", "undi", "kavali", "evaru", "ee", "mee",
    "khata", "roju", "ventane", "ippude", "kurchi", "pampandi", "dabbu", "telugulo"
}


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detects the primary language/script of the input text:
    - 'hi': Hindi (Devanagari script)
    - 'te': Telugu (Telugu script)
    - 'hinglish': Hinglish (Hindi written in Latin script)
    - 'te_rom': Romanized Telugu (Telugu written in Latin script)
    - 'en': English (default)
    
    Returns (lang_code, confidence).
    """
    if not text or not text.strip():
        return "en", 0.5

    # Check native scripts first
    devanagari_count = len(DEVANAGARI_REGEX.findall(text))
    telugu_count = len(TELUGU_SCRIPT_REGEX.findall(text))
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha > 0:
        if devanagari_count / total_alpha > 0.3:
            return "hi", 0.95
        if telugu_count / total_alpha > 0.3:
            return "te", 0.95

    # Check romanized word markers
    words = set(re.findall(r"\b[a-zA-Z]{2,}\b", text.lower()))
    if not words:
        return "en", 0.7

    hinglish_hits = len(words & HINGLISH_MARKERS)
    telugu_rom_hits = len(words & TELUGU_ROMAN_MARKERS)

    if telugu_rom_hits >= 2 or (telugu_rom_hits >= 1 and telugu_rom_hits > hinglish_hits):
        return "te_rom", 0.88
    if hinglish_hits >= 2:
        return "hinglish", 0.88

    return "en", 0.90
