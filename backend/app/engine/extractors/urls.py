import re
from typing import List, Dict, Any
from urllib.parse import urlparse

# URL extraction regex supporting schemes (http/https) and naked domains (e.g., bit.ly/xxx, netf1ix-billing.com)
URL_REGEX = re.compile(
    r"(?:https?://[^\s<>\"']+|(?:\b(?:[a-zA-Z0-9-]+\.)+(?:com|org|in|net|xyz|top|site|vip|info|co|biz|tk|ml|ga|cf|gq|link|club|online|app|dev)/?[^\s<>\"']*))",
    re.IGNORECASE,
)

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "buff.ly", "ow.ly", "cutt.ly", "rb.gy", "shorturl.at"
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "work", "date", "racing", "cam", "vip", "loan"
}

INDIAN_BRANDS_KEYWORDS = {
    "sbi", "hdfc", "icici", "axis", "pnb", "yono", "paytm", "phonepe", "gpay", "bhim",
    "incometax", "uidai", "aadhaar", "digilocker", "parivahan", "netflix", "amazon", "flipkart",
    "rbi", "npci", "sebi", "cybercrime"
}


def fold_domain_leetspeak(domain: str) -> str:
    """Folds leetspeak in domain names (e.g. netf1ix -> netflix, sb1 -> sbi)."""
    return (
        domain.replace("1", "l")
        .replace("0", "o")
        .replace("@", "a")
        .replace("5", "s")
        .replace("3", "e")
    )


OFFICIAL_DOMAINS = {
    "sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "axisbank.com", "pnbindia.in",
    "paytm.com", "phonepe.com", "airtel.in", "jio.com", "uidai.gov.in", "incometax.gov.in",
    "digilocker.gov.in", "parivahan.gov.in", "swiggy.com", "zomato.com", "flipkart.com",
    "amazon.in", "amazon.com", "netflix.com",
    "rbi.org.in", "npci.org.in", "sebi.gov.in", "cybercrime.gov.in",
}


def is_official_domain(domain: str) -> bool:
    """Checks if a domain is an authentic government or verified corporate domain."""
    if domain.endswith(".gov.in") or domain.endswith(".nic.in") or domain.endswith(".sbi"):
        return True
    for official in OFFICIAL_DOMAINS:
        if domain == official or domain.endswith(f".{official}"):
            return True
    return False


def extract_urls(text: str) -> List[Dict[str, Any]]:
    """
    Extracts URLs from text and performs lightweight static classification without network calls.
    Never visits or fetches URLs.
    """
    results: List[Dict[str, Any]] = []
    matches = URL_REGEX.findall(text)

    for match in matches:
        raw_url = match.rstrip(".,;:!?'\")>]}")
        normalized = raw_url if raw_url.startswith(("http://", "https://")) else f"http://{raw_url}"
        
        try:
            parsed = urlparse(normalized)
            domain = (parsed.hostname or "").lower()
        except Exception:
            domain = ""

        # Extract features
        is_shortener = domain in SHORTENER_DOMAINS
        tld = domain.split(".")[-1] if "." in domain else ""
        is_suspicious_tld = tld in SUSPICIOUS_TLDS
        official = is_official_domain(domain)

        folded_domain = fold_domain_leetspeak(domain)
        brand_match = None

        if official:
            is_deceptive = False
        else:
            # Brand spoof check: brand keyword present in domain, but domain is not official
            for brand in INDIAN_BRANDS_KEYWORDS:
                if brand in folded_domain:
                    brand_match = brand
                    break

            is_deceptive = bool(
                brand_match
                or is_suspicious_tld
                or "verify" in domain
                or "claim" in domain
                or "kyc" in domain
                or "billing" in domain
                or "redeem" in domain
            )

        results.append({
            "raw": raw_url,
            "normalized": normalized,
            "domain": domain,
            "is_shortener": is_shortener,
            "is_suspicious_tld": is_suspicious_tld,
            "is_official": official,
            "brand_spoof": brand_match,
            "is_deceptive": is_deceptive,
        })

    return results
