"""
Tests for the GARUDA UPI Analyzer.
Run with:  python -m pytest tests/test_upi_analyzer.py -v
"""
import pytest

from app.engine.analyzers.upi_analyzer import (
    ALWAYS_RECOMMENDATION,
    COMMON_HANDLES,
    analyze_upi,
    band,
    noisy_or,
    parse_upi,
)


# ---------------------------------------------------------------------------
# 1. User-Specified Test Cases
# ---------------------------------------------------------------------------

def test_specified_high_risk_scam():
    """
    Prompt requirement:
    'upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received' -> high
    """
    uri = "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received"
    r = analyze_upi(uri)

    assert r.valid is True
    assert r.level == "high", f"Expected 'high', got {r.level}: {r.to_dict()}"
    assert r.score >= 65
    assert ALWAYS_RECOMMENDATION in r.recommendations

    # Check triggered indicators
    codes = {i.code for i in r.indicators}
    assert "UPI_BRAND_IMPERSONATION" in codes
    assert "UPI_PREFILLED_AMOUNT" in codes
    assert "UPI_BAIT_NOTE" in codes
    # Common handle ybl should NOT trigger unknown handle
    assert "UPI_UNKNOWN_HANDLE" not in codes


def test_specified_likely_safe_payment():
    """
    Prompt requirement:
    'upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar' -> likely_safe
    """
    uri = "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar"
    r = analyze_upi(uri)

    assert r.valid is True
    assert r.level == "likely_safe", f"Expected 'likely_safe', got {r.level}: {r.to_dict()}"
    assert r.score < 25
    assert not r.indicators
    assert ALWAYS_RECOMMENDATION in r.recommendations
    assert any(sig.code == "LEGIT_COMMON_PSP" for sig in r.legitimacy_signals)


def test_specified_invalid_pa_unable_to_verify():
    """
    Prompt requirement:
    'upi://pay?pa=abc' -> unable_to_verify
    """
    uri = "upi://pay?pa=abc"
    r = analyze_upi(uri)

    assert r.valid is False
    assert r.level == "unable_to_verify", f"Expected 'unable_to_verify', got {r.level}: {r.to_dict()}"
    assert r.error is not None
    assert ALWAYS_RECOMMENDATION in r.recommendations


# ---------------------------------------------------------------------------
# 2. Recommendation Guarantee
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uri", [
    "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received",
    "upi://pay?pa=ramesh123@oksbi&pn=Ramesh Kumar",
    "upi://pay?pa=abc",
    "upi://pay?pa=someone@unknown&pn=John&am=100",
    "not a valid upi",
    "",
])
def test_always_adds_scan_to_send_recommendation(uri):
    """
    Prompt requirement:
    Always add recommendation: 'Scanning a QR code can only SEND money, never receive it.'
    """
    r = analyze_upi(uri)
    assert ALWAYS_RECOMMENDATION in r.recommendations


# ---------------------------------------------------------------------------
# 3. parse_upi() Unit Tests
# ---------------------------------------------------------------------------

def test_parse_upi_url_decoding():
    uri = "upi://pay?pa=sbi.refund%40ybl&pn=SBI%20Refund&am=4999.50&tn=refund%20received%20bonus"
    parsed = parse_upi(uri)

    assert parsed.valid is True
    assert parsed.pa == "sbi.refund@ybl"
    assert parsed.pn == "SBI Refund"
    assert parsed.am == 4999.50
    assert parsed.tn == "refund received bonus"
    assert parsed.handle == "ybl"
    assert parsed.username == "sbi.refund"

    # Both dict and attribute access must work
    assert parsed["pa"] == "sbi.refund@ybl"
    assert parsed["am"] == 4999.50


@pytest.mark.parametrize("invalid_uri", [
    "upi://pay?pa=abc",                  # missing @
    "upi://pay?pa=@ybl",                 # missing username
    "upi://pay?pa=ramesh@",              # missing handle
    "upi://pay?pa=ramesh@oksbi@ybl",     # multiple @
    "upi://pay?pn=Ramesh",               # missing pa
    "https://example.com/pay",           # not upi scheme
    "",                                  # empty
    "   ",                               # whitespace
])
def test_parse_upi_invalid_pa(invalid_uri):
    parsed = parse_upi(invalid_uri)
    assert parsed.valid is False
    assert parsed.error is not None

    r = analyze_upi(invalid_uri)
    assert r.valid is False
    assert r.level == "unable_to_verify"


# ---------------------------------------------------------------------------
# 4. Brand Impersonation Indicator Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uri,expected_word", [
    ("upi://pay?pa=hdfc.support@ybl&pn=Support", "hdfc"),
    ("upi://pay?pa=paytm.kyc@axl&pn=Verification", "paytm"),
    ("upi://pay?pa=incometax.refund@okaxis&pn=Tax Refund", "incometax"),
    ("upi://pay?pa=cashback.rewards@apl&pn=Cashback", "reward"),
    ("upi://pay?pa=user123@oksbi&pn=State Bank Helpdesk", "statebank"),
    ("upi://pay?pa=retailer@ybl&pn=Google Pay Rewards", "reward"),
])
def test_brand_impersonation_detection(uri, expected_word):
    r = analyze_upi(uri)
    codes = [i.code for i in r.indicators]
    assert "UPI_BRAND_IMPERSONATION" in codes


# ---------------------------------------------------------------------------
# 5. Pre-filled Amount Indicator Tests
# ---------------------------------------------------------------------------

def test_prefilled_amount_higher_weight_threshold():
    """
    Prompt requirement:
    UPI_PREFILLED_AMOUNT (higher if >= 2000)
    """
    low_amt_uri = "upi://pay?pa=someone123@oksbi&pn=Friend&am=500"
    high_amt_uri = "upi://pay?pa=someone123@oksbi&pn=Friend&am=2000"

    r_low = analyze_upi(low_amt_uri)
    r_high = analyze_upi(high_amt_uri)

    ind_low = next((i for i in r_low.indicators if i.code == "UPI_PREFILLED_AMOUNT"), None)
    ind_high = next((i for i in r_high.indicators if i.code == "UPI_PREFILLED_AMOUNT"), None)

    assert ind_low is not None
    assert ind_high is not None
    assert ind_high.weight > ind_low.weight
    assert ind_high.weight >= 0.35
    assert ind_low.weight <= 0.20


def test_no_prefilled_amount_indicator_when_am_missing():
    uri = "upi://pay?pa=someone123@oksbi&pn=Friend"
    r = analyze_upi(uri)
    assert not any(i.code == "UPI_PREFILLED_AMOUNT" for i in r.indicators)


# ---------------------------------------------------------------------------
# 6. Bait Note Indicator Tests (English, Hindi, Telugu)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tn,lang", [
    ("refund received", "English"),
    ("you won lottery prize", "English"),
    ("claim cashback reward", "English"),
    ("paise lo", "Hindi romanized"),
    ("inam jeeta", "Hindi romanized"),
    ("paise prapt kare", "Hindi romanized"),
    ("dabbulu teesukondi", "Telugu romanized"),
    ("bahumathi pondandi", "Telugu romanized"),
    ("venakki tirigi ravali", "Telugu romanized"),
])
def test_bait_note_detection(tn, lang):
    uri = f"upi://pay?pa=vendor@ybl&pn=Merchant&tn={tn}"
    r = analyze_upi(uri)
    assert any(i.code == "UPI_BAIT_NOTE" for i in r.indicators), f"Failed for {lang} note: {tn}"


# ---------------------------------------------------------------------------
# 7. Common vs Unknown Handle Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("handle", [
    "ybl", "ibl", "axl", "okaxis", "oksbi", "okhdfcbank", "okicici", "paytm", "ptyes", "apl", "upi"
])
def test_common_handles_not_flagged_as_unknown(handle):
    uri = f"upi://pay?pa=mohan123@{handle}&pn=Mohan Lal"
    r = analyze_upi(uri)
    assert not any(i.code == "UPI_UNKNOWN_HANDLE" for i in r.indicators)


def test_unknown_handle_is_flagged():
    uri = "upi://pay?pa=mohan123@shadycreditbank&pn=Mohan Lal"
    r = analyze_upi(uri)
    assert any(i.code == "UPI_UNKNOWN_HANDLE" for i in r.indicators)


# ---------------------------------------------------------------------------
# 8. Scoring & Bands Integrity (Weights 0.1-0.85, never 'critical')
# ---------------------------------------------------------------------------

def test_indicator_weights_within_specified_range():
    """All indicators produced by analyze_upi must have weights between 0.1 and 0.85."""
    scenarios = [
        "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received",
        "upi://pay?pa=unknown@shadybank&pn=Test&am=500&tn=test",
        "upi://pay?pa=kyc.update@axl&pn=Bank KYC&am=25000&tn=inam jeeto",
    ]
    for s in scenarios:
        r = analyze_upi(s)
        for ind in r.indicators:
            assert 0.1 <= ind.weight <= 0.85, f"Indicator {ind.code} weight {ind.weight} out of bounds"


def test_never_returns_critical():
    """
    Prompt requirement:
    never 'critical', same bands as url_analyzer
    """
    # Force high risk with all indicators firing
    extreme_scam = "upi://pay?pa=sbi.incometax.kyc@obscurehandle&pn=State Bank Refund Department&am=50000&tn=cashback refund won inam"
    r = analyze_upi(extreme_scam)

    assert r.score > 85
    assert r.level == "high"
    assert r.level != "critical"
    assert r.label == "High Risk"


def test_noisy_or_and_bands_function():
    # Test noisy-OR math
    assert noisy_or([]) == 0.0
    assert round(noisy_or([0.5, 0.5]), 4) == 0.75
    assert noisy_or([0.85]) == 0.85

    # Test band thresholds (matching url_analyzer: 65, 45, 25)
    assert band(95) == ("high", "High Risk")
    assert band(65) == ("high", "High Risk")
    assert band(64) == ("medium", "Medium Risk")
    assert band(45) == ("medium", "Medium Risk")
    assert band(44) == ("suspicious", "Suspicious")
    assert band(25) == ("suspicious", "Suspicious")
    assert band(24) == ("likely_safe", "Likely Safe")
    assert band(0) == ("likely_safe", "Likely Safe")


def test_result_to_dict_serialization():
    uri = "upi://pay?pa=sbi.refund@ybl&pn=SBI Refund&am=4999&tn=refund received"
    r = analyze_upi(uri)
    d = r.to_dict()

    assert isinstance(d, dict)
    assert d["input"] == uri
    assert d["valid"] is True
    assert d["level"] == "high"
    assert isinstance(d["indicators"], list)
    assert all(isinstance(i, dict) for i in d["indicators"])
    assert "recommendations" in d
    assert ALWAYS_RECOMMENDATION in d["recommendations"]
