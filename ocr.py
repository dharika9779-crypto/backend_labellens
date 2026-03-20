"""
ocr.py
------
Handles image upload and text extraction via OCR.Space API.
"""

import requests
import base64
import os

# ─── CONFIG ──────────────────────────────────────────────────────────────────
OCR_API_KEY = os.getenv("OCR_SPACE_API_KEY", "K81979770488957")   # ← paste your free key here
OCR_API_URL = "https://api.ocr.space/parse/image"

# ─── FALLBACK SAMPLE TEXT (used when OCR fails or no API key) ─────────────────
FALLBACK_TEXT = """
INGREDIENTS: Water, Sugar, Wheat Flour, Salt, High Fructose Corn Syrup,
Sodium Benzoate, Monosodium Glutamate (MSG), Soy Lecithin, Citric Acid,
Modified Starch, Natural Flavor, Caramel Color, Red 40, Aspartame,
Sunflower Oil, Calcium Carbonate, Ascorbic Acid, Vitamin D3.
"""


def extract_text_from_image(image_bytes: bytes, filename: str = "image.jpg") -> dict:
    """
    Sends image bytes to OCR.Space API and returns extracted text.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        filename:    Original filename (used to detect format).

    Returns:
        dict with keys:
            success (bool), text (str), error (str | None)
    """
    # Detect MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "gif": "image/gif",
                "bmp": "image/bmp", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    # Encode to base64 (OCR.Space accepts base64 strings)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "base64Image": f"data:{mime_type};base64,{b64_image}",
        "apikey": OCR_API_KEY,
        "language": "eng",
        "isOverlayRequired": False,
        "detectOrientation": True,
        "scale": True,
        "OCREngine": 2,   # Engine 2 is better for printed text / labels
    }

    try:
        response = requests.post(OCR_API_URL, data=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        # OCR.Space error check
        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Unknown OCR error"])[0]
            # Graceful fallback
            return {
                "success": False,
                "text": FALLBACK_TEXT,
                "error": f"OCR failed: {error_msg} (using fallback sample text)",
                "used_fallback": True,
            }

        # Extract text from all pages
        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return {
                "success": False,
                "text": FALLBACK_TEXT,
                "error": "No text found in image (using fallback sample text)",
                "used_fallback": True,
            }

        full_text = " ".join(
            page.get("ParsedText", "") for page in parsed_results
        ).strip()

        if not full_text:
            return {
                "success": False,
                "text": FALLBACK_TEXT,
                "error": "Empty OCR result (using fallback sample text)",
                "used_fallback": True,
            }

        return {"success": True, "text": full_text, "error": None, "used_fallback": False}

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "text": FALLBACK_TEXT,
            "error": "OCR API timed out (using fallback sample text)",
            "used_fallback": True,
        }
    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "text": FALLBACK_TEXT,
            "error": f"Network error: {str(exc)} (using fallback sample text)",
            "used_fallback": True,
        }
