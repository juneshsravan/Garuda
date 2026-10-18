import re
from typing import Tuple, Dict, Any

# Unicode range regexes for scripts per ARCHITECTURE Section 8
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")
TELUGU_SCRIPT_REGEX = re.compile(r"[\u0C00-\u0C7F]")
KANNADA_SCRIPT_REGEX = re.compile(r"[\u0C80-\u0CFF]")
TAMIL_SCRIPT_REGEX = re.compile(r"[\u0B80-\u0BFF]")
MALAYALAM_SCRIPT_REGEX = re.compile(r"[\u0D00-\u0D7F]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")

# Distinctive lexical markers for Romanized Indian languages
HINGLISH_MARKERS = {
    "aapka", "aapki", "aapko", "karo", "karein", "karna", "hoga", "jayega", "jayegi",
    "turant", "ghante", "paise", "khata", "band", "inaam", "jeet", "bhejo", "kijiye",
    "kripya", "galti", "se", "hai", "nahi", "ab", "aaj"
}

TELUGU_ROMAN_MARKERS = {
    "meeku", "vachindi", "cheyandi", "chesi", "undi", "kavali", "evaru", "ee", "mee",
    "khata", "roju", "ventane", "ippude", "kurchi", "pampandi", "dabbu", "telugulo",
    "meru", "meeru", "aiyaru", "ayyaru", "oka", "gelicharu"
}

KANNADA_ROMAN_MARKERS = {
    "nimma", "nimage", "aagide", "madi", "maadi", "beku", "hosa", "khate", "khaathe",
    "kattiri", "geddidiri", "koodale", "eegale", "thakshana", "ivatte", "sulbhadinda",
    "gelliri", "dabbina", "thamma", "neevu", "bheti", "shakhege", "labhiside"
}

TAMIL_ROMAN_MARKERS = {
    "ungal", "ungalluku", "aagividum", "seiyavum", "kadan", "pudhiya", "kanakku",
    "kattungal", "vetripettrirgal", "udanadiyaga", "ippothe", "viraindhu", "inre",
    "thambi", "seluthungal", "panam", "kilaikku", "sellavum", "parisu"
}

MALAYALAM_ROMAN_MARKERS = {
    "ningalude", "ningalkku", "aayi", "cheyyuka", "cheyyanam", "puthiya", "akkanru",
    "adakkuka", "vijayichu", "udane", "ippolthanne", "vegam", "innum", "aniyan",
    "panam", "nalkuka", "shakha", "sandarshikkuka", "sammaanam"
}

REVIEWED_LANGUAGES = {"english", "hindi", "telugu", "en", "hi", "te", "hinglish", "te_rom"}
UNREVIEWED_LANGUAGES = {"kannada", "tamil", "malayalam", "kn", "ta", "ml"}


def is_reviewed_language(lang_code: str) -> bool:
    """Checks whether the detected language has full review status or is preliminary."""
    main = (lang_code or "").split("+")[0].strip().lower()
    return main not in UNREVIEWED_LANGUAGES


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detects script and language from Unicode ranges:
    - Devanagari -> 'hindi'
    - Telugu -> 'telugu'
    - Kannada -> 'kannada'
    - Tamil -> 'tamil'
    - Malayalam -> 'malayalam'
    - Latin -> 'english' or Romanized Indic
    
    When an Indic script is accompanied by Latin tokens/links, returns mixed form:
    e.g. 'telugu+english', 'kannada+english', 'tamil+english', 'malayalam+english', 'hindi+english'.
    
    Returns (detected_language, confidence).
    """
    if not text or not text.strip():
        return "english", 0.5

    devanagari_count = len(DEVANAGARI_REGEX.findall(text))
    telugu_count = len(TELUGU_SCRIPT_REGEX.findall(text))
    kannada_count = len(KANNADA_SCRIPT_REGEX.findall(text))
    tamil_count = len(TAMIL_SCRIPT_REGEX.findall(text))
    malayalam_count = len(MALAYALAM_SCRIPT_REGEX.findall(text))
    latin_count = len(LATIN_REGEX.findall(text))

    indic_counts = [
        ("hindi", devanagari_count),
        ("telugu", telugu_count),
        ("kannada", kannada_count),
        ("tamil", tamil_count),
        ("malayalam", malayalam_count),
    ]
    top_lang, top_count = max(indic_counts, key=lambda x: x[1])

    if top_count > 0:
        # Check if code-mixed with Latin / English words
        if latin_count >= 3:
            return f"{top_lang}+english", 0.95
        return top_lang, 0.95

    # Pure Latin text: Check romanized word markers
    words = set(re.findall(r"\b[a-zA-Z]{2,}\b", text.lower()))
    if not words:
        return "english", 0.70

    marker_hits = [
        ("kannada", len(words & KANNADA_ROMAN_MARKERS)),
        ("tamil", len(words & TAMIL_ROMAN_MARKERS)),
        ("malayalam", len(words & MALAYALAM_ROMAN_MARKERS)),
        ("telugu", len(words & TELUGU_ROMAN_MARKERS)),
        ("hindi", len(words & HINGLISH_MARKERS)),
    ]
    top_roman, top_hits = max(marker_hits, key=lambda x: x[1])

    if top_hits >= 1:
        return f"{top_roman}+english", 0.88

    return "english", 0.90

