import sys
from pathlib import Path

import pytest
import yaml

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine.analyzers.qr_analyzer import analyze_qr_image, analyze_qr_payload
from app.engine.extractors.qr import encode_qr_image, validate_qr_image

GOLDEN_DIR = Path(__file__).resolve().parent
YAML_PATH = GOLDEN_DIR / "qr_expected.yaml"
IMAGES_DIR = GOLDEN_DIR / "qr_images"


def ensure_test_images(cases):
    """Generates any missing QR test images in backend/tests/golden/qr_images/."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for case in cases:
        img_path = IMAGES_DIR / case["filename"]
        if not img_path.exists():
            payload = case["payload"]
            png_bytes = encode_qr_image(payload)
            with open(img_path, "wb") as f:
                f.write(png_bytes)
            print(f"[Generated QR Image] {case['filename']} ({len(png_bytes)} bytes)")


def load_qr_cases():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


def test_qr_golden_dataset():
    cases = load_qr_cases()
    ensure_test_images(cases)

    total_passed = 0
    safe_passed = 0
    safe_total = 0

    header_line = "=" * 135
    print("\n" + header_line)
    print(
        f"{'ID':<3} | {'Case Name':<28} | {'Type':<6} | {'P-Type':<7} | {'Expected Level':<17} | {'Score':<5} | {'Actual Level':<14} | {'Status':<6} | {'Indicators / Signals'}"
    )
    print(header_line)

    results = []
    for case in cases:
        c_id = case["id"]
        c_name = case["name"]
        c_type = case["type"]
        p_type = case["payload_type"]
        expected = case["expected_level"]
        img_path = IMAGES_DIR / case["filename"]

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        # Step 1: Validate image (never store, in-memory magic-byte & size check)
        validation = validate_qr_image(img_bytes)
        assert validation["valid"] is True, f"Image {case['filename']} failed validation"

        # Step 2: In-memory decoding and analysis
        analysis = analyze_qr_image(img_bytes)

        act_score = analysis["risk"]["score"]
        act_level = analysis["risk"]["level"]
        passed = act_level in expected

        if passed:
            total_passed += 1

        if c_type == "safe":
            safe_total += 1
            if passed:
                safe_passed += 1

        indicators = [i["code"] for i in analysis["indicators"]]
        signals = [s["code"] for s in analysis["legitimacy_signals"]]

        details = []
        if indicators:
            details.append(f"Threats: {','.join(indicators)}")
        if signals:
            details.append(f"Legit: {','.join(signals)}")
        details_str = " | ".join(details) if details else "None"

        status_str = "PASS" if passed else "FAIL"
        expected_str = "/".join(expected)

        print(
            f"{c_id:<3} | {c_name:<28} | {c_type:<6} | {p_type:<7} | {expected_str:<17} | {act_score:<5} | {act_level:<14} | {status_str:<6} | {details_str[:45]}"
        )

        results.append({
            "case": case,
            "analysis": analysis,
            "passed": passed,
        })

    print(header_line)
    overall_pct = (total_passed / len(cases)) * 100
    safe_pct = (safe_passed / safe_total) * 100 if safe_total else 100
    print(
        f"Total: {total_passed}/{len(cases)} passed ({overall_pct:.1f}%) | SAFE: {safe_passed}/{safe_total} passed ({safe_pct:.1f}%)\n"
    )

    # Hard Requirements per BUILD_PLAN Section 2:
    # 1. All safe cases pass (100%)
    assert safe_passed == safe_total, f"All SAFE cases must pass! Passed {safe_passed}/{safe_total}"
    # 2. Overall pass rate >= 90%
    assert overall_pct >= 90.0, f"Overall pass rate must be at least 90%! Achieved: {overall_pct:.1f}%"


def test_surprise_upi_payloads():
    """Evaluates the 5 surprise UPI payloads against expected risk bands."""
    surprise_cases = [
        {
            "id": 1,
            "payload": "upi://pay?pa=raju.tea@oksbi&pn=Raju%20Tea%20Stall",
            "expected_label": "Likely Safe",
            "expected_levels": ["likely_safe"],
        },
        {
            "id": 2,
            "payload": "upi://pay?pa=tsspdcl.bill.pay@ybl&pn=TSSPDCL%20Official&am=1250&tn=Pay%20now%20to%20avoid%20disconnection",
            "expected_label": "High",
            "expected_levels": ["high", "critical"],
        },
        {
            "id": 3,
            "payload": "upi://pay?pa=9000000006@paytm&pn=Amazon%20Prize%20Dept&am=10&tn=Scan%20to%20receive%20Rs%205000%20prize",
            "expected_label": "High",
            "expected_levels": ["high", "critical"],
        },
        {
            "id": 4,
            "payload": "upi://pay?pa=sbi.kyc.update@axl&pn=SBI%20KYC&tn=Enter%20UPI%20PIN%20to%20verify%20KYC",
            "expected_label": "High",
            "expected_levels": ["high", "critical"],
        },
        {
            "id": 5,
            "payload": "upi://pay?pa=swiggy@icici&pn=Swiggy&am=349",
            "expected_label": "Likely Safe or Suspicious",
            "expected_levels": ["likely_safe", "suspicious"],
        },
    ]

    header_line = "=" * 135
    print("\n" + header_line)
    print("SURPRISE UPI PAYLOADS EVALUATION TABLE")
    print(header_line)
    print(
        f"{'ID':<3} | {'Payload':<50} | {'Expected Level':<26} | {'Score':<5} | {'Actual Level':<14} | {'Status':<6} | {'Indicators / Legitimacy'}"
    )
    print(header_line)

    for case in surprise_cases:
        res = analyze_qr_payload(case["payload"])
        score = res["risk"]["score"]
        level = res["risk"]["level"]
        passed = level in case["expected_levels"]

        indicators = [i["code"] for i in res["indicators"]]
        signals = [s["code"] for s in res["legitimacy_signals"]]
        details = []
        if indicators:
            details.append(f"Threats: {','.join(indicators)}")
        if signals:
            details.append(f"Legit: {','.join(signals)}")
        details_str = " | ".join(details) if details else "None"

        status_str = "PASS" if passed else "FAIL"
        disp_payload = case["payload"][:47] + "..." if len(case["payload"]) > 50 else case["payload"]

        print(
            f"{case['id']:<3} | {disp_payload:<48} | {case['expected_label']:<26} | {score:<5} | {level:<12} | {status_str:<6} | {details_str}"
        )

        assert passed, f"Surprise case {case['id']} failed: expected {case['expected_label']}, got {level} (score {score})"

    print(header_line + "\n")


def test_qr_validation_security():
    """Unit test for image format constraints, magic bytes, and size limits."""
    # Test 1: Empty payload
    with pytest.raises(ValueError, match="empty"):
        validate_qr_image(b"")

    # Test 2: Invalid magic bytes
    with pytest.raises(ValueError, match="magic-byte"):
        validate_qr_image(b"GIF89a bogus image content")

    # Test 3: Oversized image (> 5 MB)
    with pytest.raises(ValueError, match="exceeds maximum"):
        validate_qr_image(b"\x89PNG\r\n\x1a\n" + b"A" * (5 * 1024 * 1024 + 1))


if __name__ == "__main__":
    test_qr_golden_dataset()
    test_qr_validation_security()
    test_surprise_upi_payloads()
    print("[SUCCESS] All QR, security validations, and surprise UPI tests passed!")

