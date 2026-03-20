"""
barcode.py
----------
Barcode detection + Open Food Facts API
"""

import requests


def decode_barcode_from_image(image_bytes: bytes) -> dict:
    """
    Image se barcode decode karo using opencv.
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"success": False, "barcode": None,
                    "error": "Could not read image"}

        detector = cv2.barcode.BarcodeDetector()

        try:
            retval, decoded_info, decoded_type = detector.detectAndDecode(image)
        except ValueError:
            retval, decoded_info, decoded_type, _ = detector.detectAndDecode(image)

        found = bool(np.any(retval)) if hasattr(retval, '__iter__') else bool(retval)

        if found and decoded_info:
            barcodes = [b for b in decoded_info if b and str(b).strip()]
            if barcodes:
                return {"success": True, "barcode": str(barcodes[0]), "error": None}

        return {"success": False, "barcode": None,
                "error": "No barcode found — use manual entry"}

    except Exception as e:
        return {"success": False, "barcode": None, "error": str(e)}


def fetch_product_from_barcode(barcode: str) -> dict:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "LabelLens/1.0 (student project)"
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 1:
                return {
                    "success": False, "barcode": barcode,
                    "product_name": None, "ingredients_text": None,
                    "image_url": None, "brands": None,
                    "error": "Product not found in database"
                }

            product = data.get("product", {})
            ingredients_text = (
                product.get("ingredients_text_en") or
                product.get("ingredients_text") or ""
            )

            return {
                "success": True, "barcode": barcode,
                "product_name": product.get("product_name", "Unknown"),
                "brands": product.get("brands", ""),
                "ingredients_text": ingredients_text,
                "image_url": product.get("image_url", None),
                "error": None
            }

        except requests.exceptions.Timeout:
            if attempt == 2:
                return {
                    "success": False, "barcode": barcode,
                    "product_name": None, "ingredients_text": None,
                    "image_url": None, "brands": None,
                    "error": "Server timeout — try again"
                }
            continue

        except Exception as e:
            return {
                "success": False, "barcode": barcode,
                "product_name": None, "ingredients_text": None,
                "image_url": None, "brands": None,
                "error": str(e)
            }


def process_barcode_image(image_bytes: bytes) -> dict:
    barcode_result = decode_barcode_from_image(image_bytes)

    if not barcode_result["success"]:
        return {
            "success": False, "barcode": None,
            "product_name": None, "ingredients_text": None,
            "image_url": None, "brands": None,
            "error": barcode_result["error"]
        }

    return fetch_product_from_barcode(barcode_result["barcode"])
