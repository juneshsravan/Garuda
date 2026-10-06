import re
import unicodedata
from typing import Dict, Tuple

# Leetspeak and visual homoglyphs commonly used by fraudsters to bypass filters
LEET_HOMOGLYPH_MAP: Dict[str, str] = {
    "@": "a",
    "4": "a",
    "8": "b",
    "3": "e",
    "1": "i",
    "!": "i",
    "|": "i",
    "0": "o",
    "$": "s",
    "5": "s",
    "7": "t",
    "+": "t",
}

ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF\u00AD\u2060]")
WHITESPACE_REGEX = re.compile(r"\s+")


def remove_zero_width(text: str) -> str:
    """Removes hidden zero-width and invisible control characters."""
    return ZERO_WIDTH_CHARS.sub("", text)


def fold_leetspeak_word(word: str) -> str:
    """
    Folds deliberate leetspeak obfuscations in words (e.g., '0TP' -> 'otp', 'sh@re' -> 'share').
    Keeps numbers that represent actual monetary amounts or dates intact.
    Preserves trailing and leading punctuation (e.g., 'Congratulations!' stays 'congratulations!').
    """
    # If the word is a pure number or currency, leave it
    if re.fullmatch(r"[₹$€£]?\d+(?:,\d+)*(?:\.\d+)?", word):
        return word

    # Separate leading punctuation
    leading_punct = ""
    while word and word[0] in "('\"[{":
        leading_punct += word[0]
        word = word[1:]

    # Separate trailing punctuation
    trailing_punct = ""
    while word and word[-1] in "!?,.:;\"')]}":
        trailing_punct = word[-1] + trailing_punct
        word = word[:-1]

    # Specific common scam-obfuscation patterns:
    # 0TP -> otp, n0w -> now, sh@re -> share, netf1ix -> netflix
    chars = []
    for char in word:
        low = char.lower()
        if low in LEET_HOMOGLYPH_MAP and len(word) > 2:
            chars.append(LEET_HOMOGLYPH_MAP[low])
        else:
            chars.append(low)
    return leading_punct + "".join(chars) + trailing_punct


def fold_leetspeak(text: str) -> str:
    """Folds leetspeak tokens while preserving original structure."""
    tokens = text.split()
    folded = [fold_leetspeak_word(tok) for tok in tokens]
    return " ".join(folded)


def normalize_text(raw_text: str) -> Tuple[str, str]:
    """
    Performs standard Unicode NFKC normalization and cleanups.
    Returns a tuple of:
    1. clean_text: Unicode NFKC normalized text with zero-width characters removed (used for evidence).
    2. search_text: Lowercased, leetspeak-folded copy (used for rule matching).
    """
    if not raw_text:
        return "", ""

    # 1. Unicode NFKC normalization
    nfkc = unicodedata.normalize("NFKC", raw_text)

    # 2. Strip zero-width characters
    clean_text = remove_zero_width(nfkc).strip()

    # 3. Create search text (lowercased, leetspeak folded)
    search_text = fold_leetspeak(clean_text)
    search_text = WHITESPACE_REGEX.sub(" ", search_text)

    return clean_text, search_text
