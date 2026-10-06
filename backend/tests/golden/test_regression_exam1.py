import os
import sys
import yaml
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.engine.orchestrator import DetectionEngine


def test_regression_exam1_dataset():
    yaml_path = Path(__file__).resolve().parent / "regression_exam1.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    engine = DetectionEngine()
    cases = data.get("cases", [])

    passed = 0
    total = len(cases)
    results = []

    print("=" * 125)
    print(f"{'ID':<3} | {'Type':<7} | {'Expected Level':<24} | {'Score':<5} | {'Actual Level':<14} | {'Status':<6} | Indicators / Legitimacy")
    print("=" * 125)

    for case in cases:
        c_id = case["id"]
        c_type = case["type"]
        expected = case["expected_level"]
        c_text = case["text"]

        analysis = engine.analyze(c_text)
        risk = analysis["risk"]
        score = risk["score"]
        actual_level = risk["level"]

        if isinstance(expected, list):
            is_pass = actual_level in expected
            exp_str = "/".join(expected)
        else:
            is_pass = actual_level == expected
            exp_str = str(expected)

        if is_pass:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        threat_codes = [ind["code"] for ind in analysis["indicators"]]
        legit_codes = [sig["code"] for sig in analysis["legitimacy_signals"]]
        
        signal_parts = []
        if threat_codes:
            signal_parts.append(f"Threats: {','.join(threat_codes)}")
        if legit_codes:
            signal_parts.append(f"Legit: {','.join(legit_codes)}")
        signals_summary = " | ".join(signal_parts) if signal_parts else "None"

        results.append({
            "id": c_id,
            "type": c_type,
            "expected": exp_str,
            "score": score,
            "actual": actual_level,
            "status": status,
            "signals": signals_summary,
        })

        print(f"{c_id:<3} | {c_type:<7} | {exp_str:<24} | {score:<5} | {actual_level:<14} | {status:<6} | {signals_summary}")

    print("=" * 125)
    pct = (passed / total) * 100 if total > 0 else 0
    safe_cases = [r for r in results if r["type"] == "safe"]
    safe_passed = sum(1 for r in safe_cases if r["status"] == "PASS")
    safe_pct = (safe_passed / len(safe_cases)) * 100 if safe_cases else 0

    scam_cases = [r for r in results if r["type"] == "scam"]
    scam_passed = sum(1 for r in scam_cases if r["status"] == "PASS")
    scam_pct = (scam_passed / len(scam_cases)) * 100 if scam_cases else 0

    print(f"Regression Exam 1: {passed}/{total} passed ({pct:.1f}%) | GENUINE: {safe_passed}/{len(safe_cases)} passed ({safe_pct:.1f}%) | SCAMS: {scam_passed}/{len(scam_cases)} passed ({scam_pct:.1f}%)\n")
    return passed == total


if __name__ == "__main__":
    test_regression_exam1_dataset()
