import re
from typing import Any

import cv2
import numpy as np

# Maximum upload limit: 5 MB (ARCHITECTURE Section 6 & 8.8, BUILD_PLAN Chunk 9)
MAX_QR_SIZE_BYTES = 5 * 1024 * 1024

# Magic bytes signatures for supported image formats
# Strictly png / jpg / webp per ARCHITECTURE 8.8
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPG_MAGIC = b"\xff\xd8\xff"
RIFF_MAGIC = b"RIFF"
WEBP_MAGIC = b"WEBP"


def validate_qr_image(image_bytes: bytes) -> dict[str, Any]:
    """
    Validates image bytes entirely in memory.
    Enforces:
    1. Non-empty data.
    2. Size <= 5 MB.
    3. Magic-byte verification for PNG, JPEG, or WEBP.
    Never persists or stores images to disk.
    """
    if not image_bytes:
        raise ValueError("Image payload is empty.")

    size = len(image_bytes)
    if size > MAX_QR_SIZE_BYTES:
        raise ValueError(
            f"Image size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of 5 MB."
        )

    # Magic byte checks
    if image_bytes.startswith(PNG_MAGIC):
        mime_type = "image/png"
    elif image_bytes.startswith(JPG_MAGIC):
        mime_type = "image/jpeg"
    elif image_bytes.startswith(RIFF_MAGIC) and len(image_bytes) >= 12 and image_bytes[8:12] == WEBP_MAGIC:
        mime_type = "image/webp"
    else:
        raise ValueError(
            "Invalid image format. Only PNG, JPG, and WEBP formats are accepted based on magic-byte verification."
        )

    return {
        "valid": True,
        "mime_type": mime_type,
        "size_bytes": size,
    }


def decode_qr_image(image_bytes: bytes) -> str | None:
    """
    Decodes QR code from in-memory image bytes.
    Architecture 8.8:
    1. Primary: OpenCV QRCodeDetector with grayscale & adaptive thresholding passes.
    2. Fallback: pyzbar if available.
    Never writes the image to disk.
    """
    validate_qr_image(image_bytes)

    # Decode bytes to OpenCV image in memory
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image data into valid image matrix.")

    detector = cv2.QRCodeDetector()

    # Pass 1: Direct color image detection
    payload, _points, _ = detector.detectAndDecode(img)
    if payload and payload.strip():
        return payload.strip()

    # Pass 2: Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    payload, _points, _ = detector.detectAndDecode(gray)
    if payload and payload.strip():
        return payload.strip()

    # Pass 3: Otsu thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    payload, _points, _ = detector.detectAndDecode(thresh)
    if payload and payload.strip():
        return payload.strip()

    # Pass 4: Quiet zone padding (helps when QR fills entire image bounding box)
    padded = cv2.copyMakeBorder(gray, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    payload, _points, _ = detector.detectAndDecode(padded)
    if payload and payload.strip():
        return payload.strip()

    # Pass 5: pyzbar fallback (if installed and dependencies available)
    try:
        from pyzbar import pyzbar
        results = pyzbar.decode(img)
        if not results:
            results = pyzbar.decode(gray)
        if results:
            decoded_val = results[0].data.decode("utf-8", errors="replace").strip()
            if decoded_val:
                return decoded_val
    except (ImportError, OSError, RuntimeError, ValueError):
        # Graceful fallback if pyzbar C DLLs are unavailable on host environment
        pass

    return None


def classify_payload(payload: str) -> str:
    """
    Classifies decoded QR payload into one of:
    - upi   : UPI payment URI (upi://pay?...)
    - url   : HTTP/HTTPS web address or domain link
    - wifi  : Wi-Fi network configuration string (WIFI:S:...)
    - text  : Plain human-readable text
    - other : Binary, custom scheme, or unclassified structure
    """
    if not payload:
        return "other"

    cleaned = payload.strip()

    # UPI Check
    if cleaned.lower().startswith("upi://"):
        return "upi"

    # Wi-Fi Check
    if cleaned.upper().startswith("WIFI:"):
        return "wifi"

    # URL Check
    url_pattern = re.compile(
        r"^(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?$",
        re.IGNORECASE,
    )
    if cleaned.lower().startswith(("http://", "https://")) or url_pattern.match(cleaned):
        return "url"

    # Text Check: contains standard ASCII or Unicode text characters
    if any(c.isalnum() for c in cleaned):
        return "text"

    return "other"


def encode_qr_image(payload: str) -> bytes:
    """
    Generates a high-contrast PNG QR code image entirely in memory using OpenCV.
    Useful for golden tests and synthetic verification.
    """
    encoder = cv2.QRCodeEncoder_create()
    qr_mat = encoder.encode(payload)
    if qr_mat is None:
        raise RuntimeError("Failed to encode payload to QR code.")

    # Resize with nearest-neighbor to preserve sharp QR boundaries
    scale = max(6, 300 // max(qr_mat.shape[0], 1))
    target_dim = qr_mat.shape[0] * scale
    qr_scaled = cv2.resize(qr_mat, (target_dim, target_dim), interpolation=cv2.INTER_NEAREST)

    # Add a clean 25px white border (quiet zone required by QR standard)
    bordered = cv2.copyMakeBorder(qr_scaled, 25, 25, 25, 25, cv2.BORDER_CONSTANT, value=255)

    success, encoded_png = cv2.imencode(".png", bordered)
    if not success:
        raise RuntimeError("Failed to compress QR image into PNG format.")

    return encoded_png.tobytes()
