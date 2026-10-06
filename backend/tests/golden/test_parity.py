import os
import sys
import yaml
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

SUPPORTED_LANGUAGES = ["en", "hi", "te", "te_rom", "hinglish"]


def test_lexicon_parity():
    lexicon_path = Path(__file__).resolve().parent.parent.parent / "app" / "engine" / "lexicons" / "concepts.yaml"
    with open(lexicon_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Ignore metadata keys
    concepts = {k: v for k, v in data.items() if k not in ["version", "description"]}
    
    missing_report = []

    print("=" * 80)
    print("LEXICON PARITY VERIFICATION")
    print("=" * 80)

    for concept_name, lang_dict in concepts.items():
        if not isinstance(lang_dict, dict):
            missing_report.append(f"Concept '{concept_name}' is not structured as language dictionary.")
            continue

        for lang in SUPPORTED_LANGUAGES:
            terms = lang_dict.get(lang)
            if not terms or not isinstance(terms, list) or len(terms) == 0:
                missing_report.append(f"Concept '{concept_name}' is missing terms for language '{lang}'.")
            else:
                # Ensure terms are non-empty strings
                valid_terms = [t for t in terms if isinstance(t, str) and t.strip()]
                if len(valid_terms) == 0:
                    missing_report.append(f"Concept '{concept_name}' has empty term list for '{lang}'.")

    if missing_report:
        print("\n[FAIL] Lexicon Parity Gaps Detected:")
        for err in missing_report:
            print(f"  - {err}")
        print("=" * 80)
        assert False, f"Lexicon parity failed with {len(missing_report)} gaps!"
    else:
        print(f"[PASS] All {len(concepts)} concepts have complete parity across all 5 languages:")
        print(f"       {', '.join(SUPPORTED_LANGUAGES)}")
        for concept_name, lang_dict in concepts.items():
            counts = {lang: len(lang_dict[lang]) for lang in SUPPORTED_LANGUAGES}
            print(f"  - {concept_name:<24}: {counts}")
        print("=" * 80)


if __name__ == "__main__":
    test_lexicon_parity()
