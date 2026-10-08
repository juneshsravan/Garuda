import os
import sys
import yaml
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.engine.orchestrator import DetectionEngine
from app.engine.extractors.urls import is_official_domain
from app.engine.scoring.scorer import calculate_score
from app.engine.analyzers.text_rules import Indicator
from app.engine.analyzers.legitimacy import LegitimacySignal


def test_regression_real_dataset():
    """Verify genuine RBI and official advisories in regression_real.yaml."""
    yaml_path = Path(__file__).resolve().parent / "regression_real.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    engine = DetectionEngine()
    cases = data.get("cases", [])

    assert len(cases) > 0, "No test cases found in regression_real.yaml"

    for case in cases:
        c_id = case["id"]
        c_text = case["text"]
        expected_levels = case["expected_level"]
        expected_signals = case.get("expected_signals", [])

        analysis = engine.analyze(c_text)
        risk = analysis["risk"]
        score = risk["score"]
        actual_level = risk["level"]

        # 1. Level must match expected (likely_safe)
        assert actual_level in expected_levels, (
            f"Case {c_id} failed: expected {expected_levels}, got {actual_level} (score: {score})"
        )

        # 2. Legitimacy signals must NOT be empty
        legit_signals = analysis.get("legitimacy_signals", [])
        assert len(legit_signals) > 0, (
            f"Case {c_id} failed: legitimacy_signals is empty for genuine RBI message: '{c_text}'"
        )

        # 3. Check specific expected legitimacy signals
        detected_codes = {sig["code"] for sig in legit_signals}
        for exp_code in expected_signals:
            assert exp_code in detected_codes, (
                f"Case {c_id} failed: expected signal {exp_code} not found in {detected_codes}"
            )


def test_official_domains_and_subdomains():
    """Verify rbi.org.in, npci.org.in, sebi.gov.in, cybercrime.gov.in and their subdomains."""
    test_domains = [
        "rbi.org.in",
        "rbikehtahai.rbi.org.in",
        "press.rbi.org.in",
        "npci.org.in",
        "upigateway.npci.org.in",
        "sebi.gov.in",
        "scores.sebi.gov.in",
        "cybercrime.gov.in",
        "report.cybercrime.gov.in",
    ]
    for d in test_domains:
        assert is_official_domain(d) is True, f"Domain {d} should be recognized as official"

    engine = DetectionEngine()
    for d in test_domains:
        analysis = engine.analyze(f"Please check the advisory published at https://{d}/notice")
        sig_codes = {sig["code"] for sig in analysis["legitimacy_signals"]}
        assert "LEGIT_OFFICIAL_DOMAIN" in sig_codes, (
            f"URL with domain {d} must trigger LEGIT_OFFICIAL_DOMAIN"
        )


def test_multilingual_channel_advice():
    """Verify LEGIT_OFFICIAL_CHANNEL_ADVICE triggers in all 5 languages."""
    engine = DetectionEngine()
    phrases = {
        "en": "Visit your own bank branch or check official website",
        "hi": "अपनी बैंक शाखा जाएं या आधिकारिक पोर्टल देखें",
        "te": "మీ బ్యాంకు శాఖను సందర్శించండి లేదా అధికారిక వెబ్‌సైట్ చూడండి",
        "te_roman": "Sahayam kosam mee bank shakhanu sandarsinchandi",
        "hinglish": "Apni bank branch jayein aur official portal dekhe",
    }
    for lang, text in phrases.items():
        analysis = engine.analyze(text)
        sig_codes = {sig["code"] for sig in analysis["legitimacy_signals"]}
        assert "LEGIT_OFFICIAL_CHANNEL_ADVICE" in sig_codes, (
            f"Channel advice failed for language '{lang}': '{text}'"
        )


def test_anti_gaming_rule_with_rbi_links():
    """
    Ensure anti-gaming rule: no legitimacy discount if there is a credential request,
    fee demand or deceptive URL, even if scammers include official RBI links or advice.
    """
    engine = DetectionEngine()
    attack_messages = [
        # Credential solicitation with genuine RBI link
        "URGENT: Share your OTP immediately to verify your account or visit https://rbikehtahai.rbi.org.in/",
        # Fee demand with genuine RBI link and bank branch advice
        "Pay Rs 1,499 processing fee to release your loan. Visit your bank branch or https://rbikehtahai.rbi.org.in/",
        # Deceptive phishing URL alongside legitimate RBI advisory link
        "Your SBI account is suspended! Update KYC at http://sbi-kyc-update.com or check https://rbikehtahai.rbi.org.in/",
    ]

    for msg in attack_messages:
        analysis = engine.analyze(msg)
        risk = analysis["risk"]
        # Must NOT be classified as safe
        assert risk["level"] in ("medium", "high", "critical"), (
            f"Anti-gaming failed for '{msg}': classified as {risk['level']} (score: {risk['score']})"
        )

    # Unit check calculate_score directly
    leg_signals = [
        LegitimacySignal(code="LEGIT_OFFICIAL_DOMAIN", label="Official domain", weight=0.55),
        LegitimacySignal(code="LEGIT_OFFICIAL_CHANNEL_ADVICE", label="Official channel", weight=0.55),
    ]

    # 1. Credential request
    cred_ind = [Indicator(code="CRED_OTP_REQUEST", label="OTP", severity="high", weight=0.55)]
    res_cred = calculate_score(cred_ind, leg_signals)
    assert res_cred["anti_gaming_applied"] is True
    assert res_cred["raw_l"] == 0.0

    # 2. Fee demand
    fee_ind = [Indicator(code="ADVANCE_FEE", label="Fee", severity="high", weight=0.60)]
    res_fee = calculate_score(fee_ind, leg_signals)
    assert res_fee["anti_gaming_applied"] is True
    assert res_fee["raw_l"] == 0.0

    # 3. Deceptive URL
    deceptive_ind = [Indicator(code="DECEPTIVE_URL_DETECTED", label="Phish", severity="high", weight=0.55)]
    res_dec = calculate_score(deceptive_ind, leg_signals)
    assert res_dec["anti_gaming_applied"] is True
    assert res_dec["raw_l"] == 0.0
