"""
personalization.py
------------------
Rule-based personalised health recommendations based on:
  - Age group
  - Diet type
  - Medical conditions
  - Allergies
  - Detected harmful ingredients
"""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(_DATA_PATH, "r") as f:
    _DATA = json.load(f)

DIABETIC_TRIGGERS  = [i.lower() for i in _DATA["diabetic_warnings"]]
ALLERGEN_MAP       = {k: [i.lower() for i in v]
                      for k, v in _DATA["common_allergens"].items()}

# ── AGE-BASED RULES ───────────────────────────────────────────
AGE_RULES = {
    "child": {
        "avoid": [
            "aspartame", "saccharin", "acesulfame", "sucralose",
            "red 40", "yellow 5", "yellow 6", "blue 1", "blue 2",
            "sodium benzoate", "monosodium glutamate", "msg",
            "caffeine", "sodium nitrate", "sodium nitrite",
        ],
        "warnings": {
            "aspartame": "⚠️ Artificial sweeteners not recommended for children under 12.",
            "red 40": "⚠️ Artificial colors (Red 40) linked to hyperactivity in children.",
            "yellow 5": "⚠️ Yellow 5 dye may cause hyperactivity in children.",
            "sodium benzoate": "⚠️ Sodium Benzoate not recommended for children.",
            "msg": "⚠️ MSG not recommended for young children.",
        }
    },
    "teen": {
        "avoid": ["excessive sugar", "high fructose corn syrup", "trans fat"],
        "warnings": {
            "high fructose corn syrup": "⚠️ High sugar intake affects teen development and causes acne.",
        }
    },
    "senior": {
        "avoid": [
            "sodium", "salt", "sodium chloride", "sodium benzoate",
            "sodium nitrate", "monosodium glutamate", "msg",
            "trans fat", "partially hydrogenated",
        ],
        "warnings": {
            "sodium": "⚠️ High sodium increases blood pressure risk in seniors (60+).",
            "msg": "⚠️ MSG may cause adverse reactions in older adults.",
            "trans fat": "⚠️ Trans fats increase heart disease risk significantly in seniors.",
        }
    },
}

# ── DIET-BASED RULES ──────────────────────────────────────────
DIET_RULES = {
    "vegan": {
        "avoid": [
            "milk", "butter", "cheese", "cream", "lactose", "whey",
            "casein", "egg", "albumin", "gelatin", "honey",
            "carmine", "e120", "lard", "tallow", "anchovies",
        ],
        "label": "🌱 Vegan Alert",
    },
    "vegetarian": {
        "avoid": [
            "gelatin", "lard", "tallow", "anchovies", "carmine",
            "e120", "rennet", "isinglass",
        ],
        "label": "🥗 Vegetarian Alert",
    },
    "keto": {
        "avoid": [
            "sugar", "high fructose corn syrup", "maltodextrin",
            "dextrose", "glucose", "flour", "wheat", "starch",
            "modified starch", "corn syrup",
        ],
        "label": "🥩 Keto Alert",
    },
    "low_sodium": {
        "avoid": [
            "salt", "sodium", "sodium chloride", "sodium benzoate",
            "sodium nitrate", "sodium nitrite", "monosodium glutamate",
            "disodium", "sodium bicarbonate",
        ],
        "label": "🧂 Low Sodium Alert",
    },
    "low_sugar": {
        "avoid": [
            "sugar", "high fructose corn syrup", "glucose syrup",
            "fructose", "dextrose", "maltodextrin", "honey",
            "maple syrup", "corn syrup",
        ],
        "label": "🍬 Low Sugar Alert",
    },
}

# ── MEDICAL CONDITION RULES ───────────────────────────────────
MEDICAL_RULES = {
    "hypertension": {
        "avoid": [
            "salt", "sodium", "sodium chloride", "monosodium glutamate",
            "msg", "sodium benzoate", "disodium", "sodium nitrate",
            "sodium nitrite", "baking soda", "sodium bicarbonate",
        ],
        "warning_prefix": "💓 HIGH BP WARNING",
    },
    "pregnant": {
        "avoid": [
            "aspartame", "saccharin", "acesulfame", "sodium nitrate",
            "sodium nitrite", "alcohol", "caffeine", "tbhq",
            "bha", "bht", "artificial flavor", "artificial color",
        ],
        "warning_prefix": "🤰 PREGNANCY WARNING",
    },
    "heart": {
        "avoid": [
            "trans fat", "partially hydrogenated", "saturated fat",
            "sodium", "salt", "cholesterol", "lard", "tallow",
            "palm oil", "coconut oil",
        ],
        "warning_prefix": "❤️ HEART DISEASE WARNING",
    },
    "kidney": {
        "avoid": [
            "sodium", "potassium", "phosphate", "phosphorus",
            "disodium phosphate", "calcium phosphate",
            "potassium chloride", "sodium benzoate",
        ],
        "warning_prefix": "🫘 KIDNEY WARNING",
    },
    "thyroid": {
        "avoid": [
            "soy", "soybean", "tofu", "tempeh", "soy lecithin",
            "iodine", "fluoride",
        ],
        "warning_prefix": "🦋 THYROID WARNING",
    },
    "ibs": {
        "avoid": [
            "sorbitol", "mannitol", "xylitol", "lactose", "fructose",
            "high fructose corn syrup", "inulin", "chicory",
            "carrageenan", "guar gum", "xanthan gum",
        ],
        "warning_prefix": "🫃 IBS WARNING",
    },
    "celiac": {
        "avoid": [
            "wheat", "barley", "rye", "oats", "malt", "gluten",
            "wheat flour", "wheat starch", "spelt", "kamut",
        ],
        "warning_prefix": "🌾 CELIAC WARNING",
    },
}


# ── HELPERS ───────────────────────────────────────────────────
def _ingredient_names(classified: list) -> list:
    return [item["name"].lower() for item in classified]


def _matches_any(ingredient: str, trigger_list: list) -> bool:
    for trigger in trigger_list:
        if trigger in ingredient or ingredient in trigger:
            return True
    return False


# ── CHECK FUNCTIONS ───────────────────────────────────────────
def check_age_warnings(classified: list, age: str) -> list:
    warnings = []
    if age not in AGE_RULES:
        return []

    rules = AGE_RULES[age]
    avoid_list = rules.get("avoid", [])
    custom_warnings = rules.get("warnings", {})

    for item in _ingredient_names(classified):
        if _matches_any(item, avoid_list):
            # Custom warning agar hai
            for key, msg in custom_warnings.items():
                if key in item or item in key:
                    if msg not in warnings:
                        warnings.append(msg)
                    break
            else:
                # Generic warning
                age_label = {
                    "child": "children under 12",
                    "senior": "seniors (60+)"
                }.get(age, age)
                warnings.append(
                    f"⚠️ '{item.title()}' not recommended for {age_label}."
                )

    return list(dict.fromkeys(warnings))  # deduplicate


def check_diet_warnings(classified: list, diet_type: str) -> list:
    warnings = []
    if diet_type == 'none' or diet_type not in DIET_RULES:
        return []

    rules = DIET_RULES[diet_type]
    avoid_list = rules["avoid"]
    label = rules["label"]

    found = []
    for item in _ingredient_names(classified):
        if _matches_any(item, avoid_list):
            found.append(item.title())

    if found:
        warnings.append(
            f"{label}: Contains {', '.join(found[:3])} "
            f"{'and more' if len(found) > 3 else ''} "
            f"— not suitable for your diet."
        )

    return warnings


def check_medical_warnings(classified: list, medical_conditions: list) -> list:
    warnings = []

    for condition in medical_conditions:
        if condition == 'diabetes':
            continue  # handled separately
        if condition not in MEDICAL_RULES:
            continue

        rules = MEDICAL_RULES[condition]
        avoid_list = rules["avoid"]
        prefix = rules["warning_prefix"]

        found = []
        for item in _ingredient_names(classified):
            if _matches_any(item, avoid_list):
                found.append(item.title())

        if found:
            warnings.append(
                f"{prefix}: Contains {', '.join(found[:3])}"
                f"{'...' if len(found) > 3 else ''} "
                f"— potentially harmful for your condition."
            )

    return warnings


def check_diabetic_warnings(classified: list) -> list:
    warnings = []
    for item in _ingredient_names(classified):
        if _matches_any(item, DIABETIC_TRIGGERS):
            warnings.append(
                f"⚠️ '{item.title()}' may raise blood sugar levels — "
                "diabetic individuals should consume with caution."
            )
    return warnings


def check_allergy_warnings(classified: list, user_allergies: list) -> list:
    warnings = []
    ingredient_names = _ingredient_names(classified)
    user_allergies_lower = [a.lower().strip() for a in user_allergies]

    for allergy in user_allergies_lower:
        triggers = ALLERGEN_MAP.get(allergy, [allergy])
        found = []
        for ing in ingredient_names:
            if _matches_any(ing, triggers):
                found.append(ing.title())
        if found:
            warnings.append(
                f"🚨 ALLERGY ALERT ({allergy.upper()}): "
                f"Contains {', '.join(found)} — avoid if allergic!"
            )

    return warnings


def check_harmful_ingredients(classified: list) -> list:
    warnings = []
    for item in classified:
        if item["category"] == "harmful":
            warnings.append(
                f"☠️ '{item['name'].title()}' is classified as harmful "
                "and is linked to health risks."
            )
    return warnings


def get_general_advice(health_score: dict, age: str = "", diet_type: str = "") -> str:
    score = health_score.get("normalised", 50)

    if score >= 80:
        return "✅ This product looks generally safe. Enjoy in moderation."
    elif score >= 60:
        return "🟡 This product is acceptable but has some ingredients to watch."
    elif score >= 40:
        return "🟠 Consume this product cautiously. Several moderate-risk ingredients present."
    else:
        return "🔴 This product contains multiple harmful ingredients. Consider healthier alternatives."


def personalise(
    classified: list,
    health_score: dict,
    is_diabetic: bool,
    user_allergies: list,
    age: str = "adult",
    diet_type: str = "none",
    medical_conditions: list = None,
) -> dict:
    """
    Master personalisation — all checks combined.
    """
    if medical_conditions is None:
        medical_conditions = []

    diabetic_warnings  = check_diabetic_warnings(classified) if is_diabetic else []
    allergy_warnings   = check_allergy_warnings(classified, user_allergies)
    harmful_warnings   = check_harmful_ingredients(classified)
    age_warnings       = check_age_warnings(classified, age)
    diet_warnings      = check_diet_warnings(classified, diet_type)
    medical_warnings   = check_medical_warnings(classified, medical_conditions)
    general_advice     = get_general_advice(health_score, age, diet_type)

    return {
        "diabetic_warnings":  diabetic_warnings,
        "allergy_warnings":   allergy_warnings,
        "harmful_warnings":   harmful_warnings,
        "age_warnings":       age_warnings,
        "diet_warnings":      diet_warnings,
        "medical_warnings":   medical_warnings,
        "general_advice":     general_advice,
        "total_warnings": (
            len(diabetic_warnings) + len(allergy_warnings) +
            len(harmful_warnings) + len(age_warnings) +
            len(diet_warnings) + len(medical_warnings)
        ),
    }