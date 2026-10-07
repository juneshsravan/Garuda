import re
from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlparse

# Matches standard Indian UPI VPAs (e.g., help.urgent@ybl, zomato@icici)
UPI_VPA_REGEX = re.compile(
    r"\b[a-zA-Z0-9.\-_]{2,256}@(okaxis|okhdfc|okicici|oksbi|ybl|ibl|axl|paytm|apl|pingpay|upi|postbank|icici|sbi|hdfc|kotak|barodampay)\b",
    re.IGNORECASE,
)

# Matches currency representations: ₹3000, Rs. 1,450.00, Rs 5,000, 25 lakh, 5 lakh
AMOUNT_REGEX = re.compile(
    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|crore)?|\b([\d,]+)\s*(?:lakh|crore)\b",
    re.IGNORECASE,
)

# Common personal PSP handles assigned to individual retail accounts
PERSONAL_PSP_HANDLES = {
    "okhdfc", "okaxis", "okicici", "oksbi",
    "ybl", "ibl", "axl", "paytm", "apl",
    "postbank", "pingpay", "upi"
}

# Major institutions, banks, government bodies, and brands frequently impersonated
KNOWN_BRANDS_AND_AUTHORITIES = [
    "sbi", "state bank", "hdfc", "icici", "axis", "kotak", "pnb", "punjab national",
    "bank of baroda", "canara", "union bank", "income tax", "tax refund",
    "electricity", "power", "bescom", "mseb", "tneb", "uppcl", "dhbvn",
    "phonepe", "paytm", "google pay", "gpay", "amazon", "flipkart", "netflix",
    "customs", "cbi", "police", "cyber crime", "trai", "courier", "cashback", "reward"
]


def extract_upi_details(text: str) -> dict[str, Any]:
    """Extracts UPI Virtual Payment Addresses and financial amounts from text."""
    full_vpas = [m.group(0) for m in UPI_VPA_REGEX.finditer(text)]

    amounts = []
    for match in AMOUNT_REGEX.finditer(text):
        amounts.append(match.group(0).strip())

    return {
        "vpas": full_vpas,
        "amounts": amounts,
    }


def parse_upi_uri(uri: str) -> dict[str, Any]:
    """
    Parses a UPI payment URI (upi://pay?pa=...&pn=...&am=...&tn=...)
    Extracts payee VPA, payee display name, pre-filled amount, note, and query params.
    Per ARCHITECTURE Section 8.8.
    """
    if not uri or not uri.strip():
        return {
            "is_valid": False,
            "error": "Empty UPI URI provided",
            "vpa": None,
            "payee_name": None,
            "amount": None,
            "note": None,
            "params": {},
        }

    stripped = uri.strip()
    if not stripped.lower().startswith("upi://"):
        return {
            "is_valid": False,
            "error": "URI does not use upi:// scheme",
            "vpa": None,
            "payee_name": None,
            "amount": None,
            "note": None,
            "params": {},
        }

    # Handle upi://pay?... parsing
    # Use urlparse; query part contains key-value pairs
    parsed = urlparse(stripped)
    query_str = parsed.query
    if not query_str and "?" in stripped:
        query_str = stripped.split("?", 1)[1]

    raw_qs = parse_qs(query_str, keep_blank_values=True)
    params: dict[str, str] = {}
    for k, v_list in raw_qs.items():
        if v_list:
            params[k.lower()] = unquote_plus(v_list[0])

    vpa = params.get("pa", "").strip()
    payee_name = params.get("pn", "").strip()
    note = params.get("tn", "").strip()
    raw_am = params.get("am", "").strip()

    # Parse amount as float if valid numeric
    amount: float | None = None
    if raw_am:
        try:
            # Strip commas or currency prefixes if any
            clean_am = re.sub(r"[^\d.]", "", raw_am)
            if clean_am:
                amount = float(clean_am)
        except ValueError:
            amount = None

    vpa_handle = ""
    vpa_user = ""
    if "@" in vpa:
        parts = vpa.split("@", 1)
        vpa_user = parts[0].lower()
        vpa_handle = parts[1].lower()

    return {
        "is_valid": bool(vpa),
        "raw_uri": stripped,
        "vpa": vpa,
        "vpa_user": vpa_user,
        "vpa_handle": vpa_handle,
        "payee_name": payee_name,
        "amount": amount,
        "note": note,
        "merchant_code": params.get("mc", "").strip(),
        "transaction_ref": params.get("tr", "").strip(),
        "currency": params.get("cu", "INR").strip(),
        "params": params,
    }


def is_personal_handle(handle: str) -> bool:
    """Checks whether the UPI PSP handle is commonly assigned to retail/personal users."""
    return (handle or "").lower() in PERSONAL_PSP_HANDLES


def claims_brand_or_authority(name: str) -> str | None:
    """
    Checks if a payee display name claims to represent a recognized brand,
    bank, utility, or government entity.
    """
    lowered = (name or "").lower()
    for brand in KNOWN_BRANDS_AND_AUTHORITIES:
        if brand in lowered:
            return brand
    return None
