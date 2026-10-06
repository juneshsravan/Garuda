import re
from typing import List, Dict, Any

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


def extract_upi_details(text: str) -> Dict[str, Any]:
    """Extracts UPI Virtual Payment Addresses and financial amounts from text."""
    vpas = UPI_VPA_REGEX.findall(text)
    full_vpas = [m.group(0) for m in UPI_VPA_REGEX.finditer(text)]

    amounts = []
    for match in AMOUNT_REGEX.finditer(text):
        amounts.append(match.group(0).strip())

    return {
        "vpas": full_vpas,
        "amounts": amounts,
    }
