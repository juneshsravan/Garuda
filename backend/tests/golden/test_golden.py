import sys
from pathlib import Path
import pytest
import yaml

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine import engine

GOLDEN_YAML_PATH = Path(__file__).resolve().parent / "messages.yaml"


def load_golden_cases():
    with open(GOLDEN_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


def test_golden_dataset():
    cases = load_golden_cases()
    results = []
    safe_passed = 0
    safe_total = 0
    total_passed = 0

    print("\n" + "=" * 125)
    print(
        f"{'ID':<3} | {'Type':<6} | {'Expected Level':<20} | {'Score':<5} | {'Actual Level':<17} | {'Status':<6} | {'Indicators / Legitimacy'}"
    )
    print("=" * 125)

    for case in cases:
        c_id = case["id"]
        c_type = case["type"]
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
            f"{c_id:<3} | {c_type:<6} | {expected_str:<20} | {act_score:<5} | {act_level:<17} | {status_str:<6} | {details_str[:50]}"
        )

        results.append({
            "case": case,
            "analysis": analysis,
            "passed": passed,
        })

    print("=" * 125)
    overall_pct = (total_passed / len(cases)) * 100
    safe_pct = (safe_passed / safe_total) * 100 if safe_total else 100
    print(f"Total: {total_passed}/{len(cases)} passed ({overall_pct:.1f}%) | SAFE: {safe_passed}/{safe_total} passed ({safe_pct:.1f}%)\n")

    # Hard requirements:
    # 1. All SAFE cases pass (100%)
    assert safe_passed == safe_total, f"All SAFE cases must pass! Passed {safe_passed}/{safe_total}"
    # 2. Overall pass rate >= 90%
    assert overall_pct >= 90.0, f"Overall pass rate must be at least 90%! Achieved: {overall_pct:.1f}%"


if __name__ == "__main__":
    test_golden_dataset()
