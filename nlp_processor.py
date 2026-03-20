"""
nlp_processor.py
----------------
spaCy optional — agar available ho toh use karo, nahi toh basic processing.
"""

import re
from difflib import SequenceMatcher

# ── E-NUMBER DATABASE ─────────────────────────────────────────
E_NUMBERS = {
    "e100": "Curcumin (Yellow color)",
    "e102": "Tartrazine (Yellow dye) — HARMFUL",
    "e110": "Sunset Yellow — HARMFUL",
    "e120": "Carmine (Red color)",
    "e122": "Carmoisine — MODERATE",
    "e124": "Ponceau 4R — HARMFUL",
    "e127": "Erythrosine — HARMFUL",
    "e129": "Allura Red (Red 40) — HARMFUL",
    "e133": "Brilliant Blue — HARMFUL",
    "e150": "Caramel Color — MODERATE",
    "e160": "Beta Carotene — SAFE",
    "e200": "Sorbic Acid — MODERATE",
    "e202": "Potassium Sorbate — MODERATE",
    "e210": "Benzoic Acid — HARMFUL",
    "e211": "Sodium Benzoate — HARMFUL",
    "e220": "Sulfur Dioxide — HARMFUL",
    "e250": "Sodium Nitrite — HARMFUL",
    "e251": "Sodium Nitrate — HARMFUL",
    "e300": "Ascorbic Acid (Vitamin C) — SAFE",
    "e306": "Vitamin E — SAFE",
    "e320": "BHA — HARMFUL",
    "e321": "BHT — HARMFUL",
    "e330": "Citric Acid — MODERATE",
    "e407": "Carrageenan — MODERATE",
    "e412": "Guar Gum — MODERATE",
    "e415": "Xanthan Gum — MODERATE",
    "e420": "Sorbitol — MODERATE",
    "e421": "Mannitol — MODERATE",
    "e471": "Mono and Diglycerides — MODERATE",
    "e500": "Sodium Bicarbonate — SAFE",
    "e621": "Monosodium Glutamate (MSG) — HARMFUL",
    "e951": "Aspartame — HARMFUL",
    "e954": "Saccharin — HARMFUL",
    "e955": "Sucralose — HARMFUL",
    "e960": "Steviol Glycosides (Stevia) — MODERATE",
}

OCR_CORRECTIONS = {
    "sugr": "sugar", "shugar": "sugar",
    "whaet": "wheat", "flor": "flour",
    "flowr": "flour", "sallt": "salt",
    "watr": "water", "watter": "water",
    "milck": "milk", "mlk": "milk",
    "buttr": "butter", "sirup": "syrup",
    "flavour": "flavor", "colour": "color",
    "sulphur": "sulfur", "sulphite": "sulfite",
    "colouring": "coloring", "flavouring": "flavoring",
}

IGNORE_WORDS = {
    'ingredients', 'contains', 'ingredient',
    'nutrition', 'facts', 'serving', 'size',
    'amount', 'daily', 'value', 'total', 'per'
}


def correct_ocr_typos(text: str) -> str:
    words = text.lower().split()
    corrected = []
    for word in words:
        clean = re.sub(r'[^a-z]', '', word)
        corrected.append(OCR_CORRECTIONS.get(clean, word))
    return ' '.join(corrected)


def extract_e_numbers(text: str) -> list:
    found = []
    pattern = re.finditer(r'\b[eE][-\s]?(\d{3,4}[a-zA-Z]?)\b', text)
    for match in pattern:
        e_code = f"e{match.group(1).lower()}"
        description = E_NUMBERS.get(e_code, f"E{match.group(1)} (Food Additive)")
        if "HARMFUL" in description:
            category = "harmful"
        elif "MODERATE" in description:
            category = "moderate"
        elif "SAFE" in description:
            category = "safe"
        else:
            category = "moderate"
        found.append({
            "name": f"E{match.group(1)} — {description.split(' — ')[0]}",
            "category": category,
            "original": match.group(0),
        })
    return found


def extract_basic(text: str) -> list:
    """Basic extraction without spaCy — split by comma/semicolon."""
    text_no_e = re.sub(r'\b[eE][-\s]?\d{3,4}[a-zA-Z]?\b', '', text)
    items = re.split(r'[,;]', text_no_e)
    result = []
    for item in items:
        clean = re.sub(r'[^a-z\s]', '', item.lower()).strip()
        if clean and len(clean) > 2 and clean not in IGNORE_WORDS:
            result.append(clean)
    return list(dict.fromkeys(result))


def extract_with_spacy(text: str) -> list:
    """Try spaCy — fallback to basic if not available."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        text_no_e = re.sub(r'\b[eE][-\s]?\d{3,4}[a-zA-Z]?\b', '', text)
        doc = nlp(text_no_e)
        extracted = []
        for chunk in doc.noun_chunks:
            clean = re.sub(r'[^a-z\s]', '', chunk.text.lower()).strip()
            if 2 < len(clean) < 50 and clean not in IGNORE_WORDS:
                extracted.append(clean)
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop and len(token.text) > 2:
                clean = re.sub(r'[^a-z\s]', '', token.text.lower()).strip()
                if clean and clean not in extracted and clean not in IGNORE_WORDS:
                    extracted.append(clean)
        return list(set(extracted))
    except Exception:
        return extract_basic(text)


def fuzzy_correct(ingredient: str, known_ingredients: list, threshold: float = 0.75) -> str:
    best_match = ingredient
    best_score = 0
    for known in known_ingredients:
        score = SequenceMatcher(None, ingredient.lower(), known.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = known
    return best_match


def nlp_process(raw_text: str, known_ingredients: list = None) -> dict:
    if known_ingredients is None:
        known_ingredients = []

    corrected = correct_ocr_typos(raw_text)
    corrections_made = corrected != raw_text.lower()
    e_numbers = extract_e_numbers(raw_text)

    # Try spaCy — auto fallback to basic
    spacy_ingredients = extract_with_spacy(corrected)

    if known_ingredients:
        final_ingredients = [fuzzy_correct(i, known_ingredients) for i in spacy_ingredients]
    else:
        final_ingredients = spacy_ingredients

    final_ingredients = list(dict.fromkeys(final_ingredients))

    return {
        "corrected_text": corrected,
        "ingredients": final_ingredients,
        "e_numbers": e_numbers,
        "corrections_made": corrections_made,
        "total_found": len(final_ingredients) + len(e_numbers),
    }
