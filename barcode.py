"""
barcode.py
----------
Barcode detection using OpenCV + Open Food Facts API
"""

import requests
import cv2
import pyzxing


def decode_barcode_from_image(image_bytes: bytes) -> dict:
    try:
        import pyzxing
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            reader = pyzxing.BarCodeReader()
            barcode = reader.decode(tmp_path)

            if barcode and barcode.raw:
                return {"success": True, "barcode": barcode.raw, "error": None}
            else:
                return {"success": False, "barcode": None,
                        "error": "No barcode found — try manual entry"}
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        return {"success": False, "barcode": None, "error": str(e)}
def fetch_product_from_barcode(barcode: str) -> dict:
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "LabelLens/1.0 (student project)"
        })
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 1:
            return {
                "success": False,
                "barcode": barcode,
                "product_name": None,
                "ingredients_text": None,
                "image_url": None,
                "brands": None,
                "error": "Product not found in Open Food Facts database"
            }

        product = data.get("product", {})
        ingredients_text = (
            product.get("ingredients_text_en") or
            product.get("ingredients_text") or
            ""
        )

        return {
            "success": True,
            "barcode": barcode,
            "product_name": product.get("product_name", "Unknown Product"),
            "brands": product.get("brands", ""),
            "ingredients_text": ingredients_text,
            "image_url": product.get("image_url", None),
            "error": None
        }

    except requests.exceptions.Timeout:
        return {"success": False, "barcode": barcode, "product_name": None,
                "ingredients_text": None, "image_url": None, "brands": None,
                "error": "API timeout"}
    except Exception as e:
        return {"success": False, "barcode": barcode, "product_name": None,
                "ingredients_text": None, "image_url": None, "brands": None,
                "error": str(e)}


def process_barcode_image(image_bytes: bytes) -> dict:
    barcode_result = decode_barcode_from_image(image_bytes)

    if not barcode_result["success"]:
        return {
            "success": False,
            "barcode": None,
            "product_name": None,
            "ingredients_text": None,
            "image_url": None,
            "brands": None,
            "error": barcode_result["error"]
        }

    return fetch_product_from_barcode(barcode_result["barcode"])