"""
processing.py
-------------
Cleans raw OCR text and extracts the ingredients list.
"""

import re


# ─── SECTION KEYWORDS ────────────────────────────────────────────────────────
# These words signal the start of the ingredients section on a label
INGREDIENT_SECTION_KEYWORDS = [
    "ingredients:", "ingredients :", "ingredient:", "contains:",
    "made with:", "made from:", "composition:", "contents:",
    "ingr\u00e9dients:",  # French label handling
]

# These words often mark the END of the ingredients section
END_SECTION_KEYWORDS = [
    "nutrition facts", "nutritional information", "allergen",
    "manufactured by", "distributed by", "produced by",
    "best before", "expiry", "net weight", "serving size",
    "amount per serving", "calories", "total fat",
]


def extract_ingredients_text(raw_text: str) -> str:
    """
    From raw OCR output, isolate just the ingredients block.

    Strategy:
    1. Lowercase everything.
    2. Find the first occurrence of 'ingredients:' (or similar).
    3. Grab everything after it until a known end-keyword or end of text.

    Returns the raw ingredients substring (not yet split into a list).
    """
    text = raw_text.lower()

    # Attempt to find the start marker
    start_idx = -1
    for keyword in INGREDIENT_SECTION_KEYWORDS:
        idx = text.find(keyword)
        if idx != -1:
            start_idx = idx + len(keyword)
            break

    # If no marker found, use the whole text (OCR might have missed the heading)
    if start_idx == -1:
        ingredients_text = text
    else:
        ingredients_text = text[start_idx:]

    # Trim at the first end-section keyword
    for end_kw in END_SECTION_KEYWORDS:
        end_idx = ingredients_text.find(end_kw)
        if end_idx != -1:
            ingredients_text = ingredients_text[:end_idx]

    return ingredients_text.strip()


def split_ingredients(ingredients_text: str) -> list[str]:
    """
    Split the ingredients block into individual ingredient strings.

    Handles:
    - Comma-separated lists
    - Semicolon-separated lists
    - Parenthetical sub-ingredients: e.g. "flour (wheat, barley)"
    - Extra whitespace and newlines from OCR
    - Percentage annotations: "sugar (15%)"
    - Trailing punctuation and asterisks
    """
    # Replace common OCR artifacts
    text = ingredients_text
    text = re.sub(r"\s+", " ", text)          # collapse whitespace / newlines
    text = re.sub(r"[*†‡§¶]", "", text)       # remove footnote symbols
    text = re.sub(r"\d+(\.\d+)?%", "", text)  # remove percentages  e.g. 12%
    text = re.sub(r"\(e\d+\)", "", text)       # remove EU additive codes e.g. (E102)
    text = re.sub(r"e\d{3,4}", "", text)       # bare E-numbers without parens

    # Flatten sub-ingredient parentheses:
    # "sunflower oil (contains: antioxidant)" → keep parent item only
    # We keep the content inside parentheses as separate items so they get classified
    text = re.sub(r"\(([^)]+)\)", r", \1,", text)  # expand parens into flat list

    # Split on comma or semicolon
    raw_items = re.split(r"[,;]", text)

    cleaned = []
    for item in raw_items:
        item = item.strip(" .:-'\"\n\t")
        item = re.sub(r"\s+", " ", item)  # normalise internal spaces
        if len(item) > 1:                  # skip single characters / empty
            cleaned.append(item)

    return cleaned


def clean_and_extract(raw_text: str) -> dict:
    """
    Full pipeline: raw OCR text → cleaned ingredients list.

    Returns:
        dict with:
            ingredients_raw_block (str)  – the raw section found
            ingredients_list     (list)  – cleaned individual items
    """
    ingredients_block = extract_ingredients_text(raw_text)
    ingredients_list  = split_ingredients(ingredients_block)

    return {
        "ingredients_raw_block": ingredients_block,
        "ingredients_list": ingredients_list,
    }

def clean_and_extract_nlp(raw_text: str) -> dict:
    """
    Enhanced pipeline — basic extraction + spaCy NLP dono use karo.
    """
    try:
        from nlp_processor import nlp_process
        import json, os

        # Known ingredients load karo data.json se
        data_path = os.path.join(os.path.dirname(__file__), "data.json")
        with open(data_path) as f:
            data = json.load(f)

        known = (
            data["ingredients"]["safe"] +
            data["ingredients"]["moderate"] +
            data["ingredients"]["harmful"]
        )

        # Basic extraction pehle
        basic = clean_and_extract(raw_text)

        # NLP se aur ingredients nikalo
        nlp_result = nlp_process(raw_text, known_ingredients=known)

        # Dono combine karo — duplicates remove
        combined = list(dict.fromkeys(
            basic["ingredients_list"] + nlp_result["ingredients"]
        ))

        return {
            "ingredients_raw_block": basic["ingredients_raw_block"],
            "ingredients_list": combined,
            "e_numbers": nlp_result["e_numbers"],
            "corrections_made": nlp_result["corrections_made"],
            "corrected_text": nlp_result["corrected_text"],
            "nlp_used": True,
        }

    except Exception as e:
        print(f"NLP failed: {e} — using basic extraction")

        import traceback
    traceback.print_exc()  # ← yeh add karo
    basic = clean_and_extract(raw_text)
    return {**basic, "nlp_used": False, "e_numbers": []}
        