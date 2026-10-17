"""Tests for the GARUDA URL analyzer.  Run with:  python -m pytest -v"""
import pytest

from app.engine.analyzers.url_analyzer import analyze_url, registered_domain

SAFE = ["sbi.co.in", "https://www.hdfcbank.com", "https://www.irctc.co.in",
        "https://myaadhaar.uidai.gov.in", "https://rbikehtahai.rbi.org.in/telugu/index.html",
        "google.com", "https://www.amazon.in/deals", "https://www.mistake.com"]

HIGH = ["http://sbi-kyc-update.xyz/login", "http://hdfc-netbanking-verify.top/login",
        "http://192.168.1.5/paytm/verify", "http://paytm.secure-update.click/upi?pin=1",
        "http://amaz0n-offers.in", "http://netf1ix-billing.com", "https://flipkrat.com/sale",
        "https://indian.1xbet.com", "https://parimatch.in"]

INVALID = ["xxx videos.com", "not a url", "", "   ", "ftp://files.example.com", "localhost"]


@pytest.mark.parametrize("url", SAFE)
def test_official_and_normal_sites_are_likely_safe(url):
    r = analyze_url(url)
    assert r.valid
    assert r.level == "likely_safe", r.to_dict()


@pytest.mark.parametrize("url", HIGH)
def test_scam_and_betting_links_are_high(url):
    r = analyze_url(url)
    assert r.level == "high", r.to_dict()
    assert r.indicators, "a high result must explain why"


@pytest.mark.parametrize("url", INVALID)
def test_invalid_input_is_never_scored_safe(url):
    r = analyze_url(url)
    assert not r.valid
    assert r.level == "unable_to_verify"
    assert r.error


def test_short_link_is_suspicious_not_high():
    assert analyze_url("https://bit.ly/3abcXYZ").level == "suspicious"


def test_betting_category_and_list_named():
    r = analyze_url("https://indian.1xbet.com")
    assert r.category == "gambling"
    assert "betting" in r.verification_status


def test_adult_site_is_medium_restricted():
    r = analyze_url("https://www.xvideos.com")
    assert r.level == "medium" and r.category == "adult"


def test_punycode_is_flagged():
    r = analyze_url("http://xn--pple-43d.com")
    assert any(i.code == "URL_PUNYCODE" for i in r.indicators)


def test_score_never_reaches_100():
    r = analyze_url("http://sbi-kyc-update.xyz/login/verify?otp=1&pin=2")
    assert r.score < 100


@pytest.mark.parametrize("host,expected", [
    ("indian.1xbet.com", "1xbet.com"), ("www.sbi.co.in", "sbi.co.in"),
    ("myaadhaar.uidai.gov.in", "uidai.gov.in"), ("192.168.1.5", "192.168.1.5")])
def test_registered_domain(host, expected):
    assert registered_domain(host) == expected
