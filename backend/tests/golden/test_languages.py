import sys
from pathlib import Path
import pytest
import yaml

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine import engine

LANGUAGES_DIR = Path(__file__).resolve().parent / "languages"


def run_language_suite(lang_name: str, yaml_filename: str):
    file_path = LANGUAGES_DIR / yaml_filename
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cases = data["cases"]
    total_passed = 0
    safe_passed = 0
    safe_total = 0

    print("\n" + "=" * 125)
    print(f"EVALUATION SUITE: {lang_name.upper()} ({len(cases)} test cases)")
    print("=" * 125)
    print(
        f"{'ID':<18} | {'Type':<6} | {'Subtype':<14} | {'Expected Level':<17} | {'Score':<5} | {'Actual Level':<17} | {'Status':<6} | {'Indicators / Legitimacy'}"
    )
    print("-" * 125)

    for case in cases:
        c_id = case["id"]
        c_type = case["type"]
        c_sub = case.get("subtype", "unknown")
        c_text = case["text"]
        expected = case["expected_level"]

        analysis = engine.analyze(c_text)
        act_score = analysis["risk"]["score"]
        act_level = analysis["risk"]["level"]

        passed = act_level in expected
        if passed:
            total_passed += 1

        if c_type == "safe":
            safe_total += 1
            if passed:
                safe_passed += 1

        indicators = [ind["code"] for ind in analysis["indicators"]]
        legit = [leg["code"] for leg in analysis["legitimacy_signals"]]

        details = []
        if indicators:
            details.append(f"Threats: {','.join(indicators)}")
        if legit:
            details.append(f"Legit: {','.join(legit)}")
        details_str = " | ".join(details) if details else "None"

        status_str = "PASS" if passed else "FAIL"
        expected_str = "/".join(expected)

        print(
            f"{c_id:<18} | {c_type:<6} | {c_sub:<14} | {expected_str:<17} | {act_score:<5} | {act_level:<17} | {status_str:<6} | {details_str[:40]}"
        )

    print("=" * 125)
    overall_pct = (total_passed / len(cases)) * 100
    safe_pct = (safe_passed / safe_total) * 100 if safe_total else 100
    print(
        f"{lang_name.upper()} RESULT: {total_passed}/{len(cases)} passed ({overall_pct:.1f}%) | "
        f"GENUINE: {safe_passed}/{safe_total} passed ({safe_pct:.1f}%)\n"
    )

    # Invariants:
    # 1. No genuine message may fail anywhere
    assert safe_passed == safe_total, f"All GENUINE cases in {lang_name} must pass! Passed {safe_passed}/{safe_total}"
    # 2. Overall pass rate >= 90%
    assert overall_pct >= 90.0, f"Overall pass rate in {lang_name} must be >= 90%! Passed {total_passed}/{len(cases)}"
    return total_passed == len(cases)


def test_kannada_language_suite():
    assert run_language_suite("Kannada", "kannada.yaml")


def test_tamil_language_suite():
    assert run_language_suite("Tamil", "tamil.yaml")


def test_malayalam_language_suite():
    assert run_language_suite("Malayalam", "malayalam.yaml")


def test_fuzzy_matching_and_short_words_exclusion():
    from app.engine.analyzers.concept_rules import is_damerau_levenshtein_1, find_lexicon_match, ENGLISH_WORDS

    # 1. Edit distance with transpositions
    assert is_damerau_levenshtein_1("ventane", "ventaney")  # insertion
    assert is_damerau_levenshtein_1("ventane", "ventne")   # deletion
    assert is_damerau_levenshtein_1("ventane", "vetnane")  # transposition
    assert is_damerau_levenshtein_1("ventane", "ventxne")  # substitution
    assert not is_damerau_levenshtein_1("ventane", "ventxyz")  # distance > 1

    # 2. Match a romanized word of 5+ letters with 1 edit distance typo
    # 'ventane' has typo 'ventaney' -> should match
    m = find_lexicon_match(["ventane"], "Eppudu ventaney cheyandi")
    assert m is not None

    # 3. Short words (< 5 letters) or English words (e.g. OTP, PIN) must NEVER fuzzy match
    # 'opt' is typo of 'otp' (len 3), but must NOT match 'otp'
    m_short = find_lexicon_match(["otp"], "Your opt has arrived")
    assert m_short is None

    # 'pinn' is typo of 'pin' (len 3), but must NOT match 'pin'
    m_pin = find_lexicon_match(["pin"], "Enter your pinn now")
    assert m_pin is None


def test_unreviewed_language_support_and_confidence():
    from app.engine.normalize import detect_language, is_reviewed_language

    # Kannada unreviewed
    lang, conf = detect_language("ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗಲಿದೆ. ತಕ್ಷಣ ಪ್ಯಾನ್ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ http://bit.ly/kannada-bank")
    assert "kannada" in lang
    assert not is_reviewed_language(lang)

    res = engine.analyze("ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗಲಿದೆ. ತಕ್ಷಣ ಪ್ಯಾನ್ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ http://bit.ly/kannada-bank")
    assert "Language support is preliminary" in res["summary"]
    # Confidence is lowered for unreviewed language
    assert res["confidence"] <= 0.75

    # English / Hindi / Telugu are reviewed
    lang_te, _ = detect_language("మీ ఖాతా బ్లాక్ అయింది")
    assert "telugu" in lang_te
    assert is_reviewed_language(lang_te)

    res_te = engine.analyze("Dear customer your account will be suspended today. Update PAN immediately: http://bit.ly/test-bank")
    assert "Language support is preliminary" not in res_te["summary"]


def test_script_detection_by_unicode_range_and_mixed():
    from app.engine.normalize import detect_language

    # Devanagari
    lang_hi, _ = detect_language("बिजली बिल जमा करें")
    assert lang_hi == "hindi"

    # Telugu + English
    lang_te_mix, _ = detect_language("మీ YONO account block అవుతుంది click link")
    assert lang_te_mix == "telugu+english"

    # Kannada + English
    lang_kn_mix, _ = detect_language("ನಿಮ್ಮ SBI account block ಆಗಿದೆ link click ಮಾಡಿ")
    assert lang_kn_mix == "kannada+english"

    # Tamil + English
    lang_ta_mix, _ = detect_language("உங்கள் bank account suspend செய்யப்பட்டுள்ளது click link")
    assert lang_ta_mix == "tamil+english"

    # Malayalam + English
    lang_ml_mix, _ = detect_language("നിങ്ങളുടെ SBI account blocked ആയിട്ടുണ്ട് click link")
    assert lang_ml_mix == "malayalam+english"

    # Pure Latin English
    lang_en, _ = detect_language("Dear customer, your bank account is blocked.")
    assert lang_en == "english"


if __name__ == "__main__":
    test_kannada_language_suite()
    test_tamil_language_suite()
    test_malayalam_language_suite()
    test_fuzzy_matching_and_short_words_exclusion()
    test_unreviewed_language_support_and_confidence()
    test_script_detection_by_unicode_range_and_mixed()

