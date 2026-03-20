"""
nlp_processor.py
----------------
spaCy se better ingredient extraction
"""

import spacy
import re
from difflib import SequenceMatcher

# ── LOAD MODEL ────────────────────────────────────────────────
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

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

# ── COMMON OCR MISTAKES ───────────────────────────────────────
OCR_CORRECTIONS = {
    "sugr": "sugar",
    "shugar": "sugar",
    "whaet": "wheat",
    "flor": "flour",
    "flowr": "flour",
    "sallt": "salt",
    "watr": "water",
    "watter": "water",
    "milck": "milk",
    "mlk": "milk",
    "buttr": "butter",
    "sirup": "syrup",
    "flavour": "flavor",
    "colour": "color",
    "sulphur": "sulfur",
    "sulphite": "sulfite",
    "colouring": "coloring",
    "flavouring": "flavoring",
}

IGNORE_WORDS = {'ingredients', 'contains', 'ingredient',
                'nutrition', 'facts', 'serving', 'size',
                'amount', 'daily', 'value', 'total', 'per'}

# ── HELPER FUNCTIONS ──────────────────────────────────────────

def correct_ocr_typos(text: str) -> str:
    """Common OCR typos fix karo."""
    words = text.lower().split()
    corrected = []
    for word in words:
        clean = re.sub(r'[^a-z]', '', word)
        if clean in OCR_CORRECTIONS:
            corrected.append(OCR_CORRECTIONS[clean])
        else:
            corrected.append(word)
    return ' '.join(corrected)


def extract_e_numbers(text: str) -> list:
    """E-numbers detect karo aur category batao."""
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


def extract_with_spacy(text: str) -> list:
    """spaCy se noun phrases extract karo."""
    text_no_e = re.sub(r'\b[eE][-\s]?\d{3,4}[a-zA-Z]?\b', '', text)
    doc = nlp(text_no_e)

    extracted = []

    for chunk in doc.noun_chunks:
        clean = chunk.text.strip().lower()
        clean = re.sub(r'[^a-z\s]', '', clean).strip()
        if 2 < len(clean) < 50 and clean not in IGNORE_WORDS:
            extracted.append(clean)

    for token in doc:
        if (
            token.pos_ in ['NOUN', 'PROPN'] and
            not token.is_stop and
            len(token.text) > 2
        ):
            clean = token.text.lower().strip()
            clean = re.sub(r'[^a-z\s]', '', clean).strip()
            if clean and clean not in extracted and clean not in IGNORE_WORDS:
                extracted.append(clean)

    return list(set(extracted))


def fuzzy_correct(ingredient: str, known_ingredients: list,
                  threshold: float = 0.75) -> str:
    """Fuzzy match karo known ingredients se."""
    best_match = ingredient
    best_score = 0

    for known in known_ingredients:
        score = SequenceMatcher(None, ingredient.lower(), known.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = known

    return best_match


# ── MAIN FUNCTION ─────────────────────────────────────────────

def nlp_process(raw_text: str, known_ingredients: list = None) -> dict:
    """
    Full NLP pipeline:
    1. OCR typos correct karo
    2. E-numbers extract karo
    3. spaCy noun phrases nikalo
    4. Fuzzy matching karo
    """
    if known_ingredients is None:
        known_ingredients = []

    # Step 1: Typo correction
    corrected = correct_ocr_typos(raw_text)
    corrections_made = corrected != raw_text.lower()

    # Step 2: E-numbers
    e_numbers = extract_e_numbers(raw_text)

    # Step 3: spaCy extraction
    spacy_ingredients = extract_with_spacy(corrected)

    # Step 4: Fuzzy match
    if known_ingredients:
        final_ingredients = []
        for ing in spacy_ingredients:
            matched = fuzzy_correct(ing, known_ingredients)
            final_ingredients.append(matched)
    else:
        final_ingredients = spacy_ingredients

    # Remove duplicates
    final_ingredients = list(dict.fromkeys(final_ingredients))

    return {
        "corrected_text": corrected,
        "ingredients": final_ingredients,
        "e_numbers": e_numbers,
        "corrections_made": corrections_made,
        "total_found": len(final_ingredients) + len(e_numbers),
    }