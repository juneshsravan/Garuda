import re
from typing import List

# Indian 10-digit mobile number starting with 6, 7, 8, 9
INDIAN_PHONE_REGEX = re.compile(
    r"(?:\+91[\-\s]?)?[6-9]\d{9}\b"
)


def extract_phone_numbers(text: str) -> List[str]:
    """Extracts phone numbers from message text."""
    matches = INDIAN_PHONE_REGEX.findall(text)
    return [m.strip() for m in matches]
