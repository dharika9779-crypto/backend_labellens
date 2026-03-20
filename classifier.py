"""
classifier.py
-------------
Matches extracted ingredients against our dataset and computes a health score.
"""

import json
import os
from difflib import SequenceMatcher


# ─── LOAD DATASET ────────────────────────────────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(_DATA_PATH, "r") as f:
    _DATA = json.load(f)

SAFE_LIST     = [i.lower() for i in _DATA["ingredients"]["safe"]]
MODERATE_LIST = [i.lower() for i in _DATA["ingredients"]["moderate"]]
HARMFUL_LIST  = [i.lower() for i in _DATA["ingredients"]["harmful"]]

# ─── SCORING ─────────────────────────────────────────────────────────────────
SCORE_MAP = {"safe": 1, "moderate": 0, "harmful": -2, "unknown": 0}


def _similarity(a: str, b: str) -> float:
    """Return 0-1 similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def _fuzzy_match(ingredient: str, word_list: list[str], threshold: float = 0.82) -> bool:
    """
    Return True if 'ingredient' fuzzy-matches any item in word_list.
    Also returns True on exact substring match (handles multi-word ingredients).
    """
    ing = ingredient.lower().strip()
    for item in word_list:
        # Exact substring match (e.g. "high fructose corn syrup" ⊆ label text)
        if item in ing or ing in item:
            return True
        # Fuzzy similarity for typos / OCR errors
        if _similarity(ing, item) >= threshold:
            return True
    return False


def classify_ingredient(ingredient: str) -> str:
    """
    Classify a single ingredient string as 'safe', 'moderate', 'harmful', or 'unknown'.

    Priority: harmful > moderate > safe > unknown
    (We surface harmful first for safety.)
    """
    if _fuzzy_match(ingredient, HARMFUL_LIST):
        return "harmful"
    if _fuzzy_match(ingredient, MODERATE_LIST):
        return "moderate"
    if _fuzzy_match(ingredient, SAFE_LIST):
        return "safe"
    return "unknown"


def classify_all(ingredients_list: list[str]) -> list[dict]:
    """
    Classify every ingredient in the list.

    Returns a list of dicts:
        [{"name": "sugar", "category": "safe"}, ...]
    """
    results = []
    for ingredient in ingredients_list:
        category = classify_ingredient(ingredient)
        results.append({"name": ingredient, "category": category})
    return results


def compute_health_score(classified: list[dict]) -> dict:
    """
    Compute an overall health score from classified ingredients.

    Scoring:
        safe     → +1
        moderate →  0
        harmful  → -2
        unknown  →  0

    Final score is clamped to [0, 100] using a normalised scale.
    Also returns a letter grade and a short verdict.

    Returns dict with: raw_score, max_possible, normalised (0-100), grade, verdict
    """
    if not classified:
        return {
            "raw_score": 0, "max_possible": 0,
            "normalised": 0, "grade": "N/A", "verdict": "No ingredients found"
        }

    raw  = sum(SCORE_MAP.get(item["category"], 0) for item in classified)
    # Max possible: every ingredient is safe (+1 each)
    maxi = len(classified)
    # Worst possible: every ingredient is harmful (-2 each)
    mini = -2 * len(classified)

    # Map raw from [mini, maxi] to [0, 100]
    if maxi == mini:
        normalised = 50
    else:
        normalised = int(((raw - mini) / (maxi - mini)) * 100)

    normalised = max(0, min(100, normalised))  # clamp

    # Grade
    if normalised >= 80:
        grade, verdict = "A", "Excellent – mostly safe ingredients"
    elif normalised >= 60:
        grade, verdict = "B", "Good – a few things to watch"
    elif normalised >= 40:
        grade, verdict = "C", "Fair – moderate concern"
    elif normalised >= 20:
        grade, verdict = "D", "Poor – several harmful ingredients"
    else:
        grade, verdict = "F", "Dangerous – many harmful ingredients"

    return {
        "raw_score": raw,
        "max_possible": maxi,
        "normalised": normalised,
        "grade": grade,
        "verdict": verdict,
    }


def full_analysis(ingredients_list: list[str]) -> dict:
    """
    Run classify_all + compute_health_score in one call.
    Returns classified list + score dict.
    """
    classified   = classify_all(ingredients_list)
    health_score = compute_health_score(classified)

    # Summary counts
    counts = {"safe": 0, "moderate": 0, "harmful": 0, "unknown": 0}
    for item in classified:
        counts[item["category"]] += 1

    return {
        "classified": classified,
        "counts": counts,
        "health_score": health_score,
    }
def full_analysis_with_enumbers(
    ingredients_list: list[str],
    e_numbers: list[dict] = None
) -> dict:
    """
    Normal analysis + E-numbers bhi include karo.
    """
    # Normal classification
    result = full_analysis(ingredients_list)

    # E-numbers add karo
    if e_numbers:
        for e in e_numbers:
            result["classified"].append({
                "name": e["name"],
                "category": e["category"]
            })
            result["counts"][e["category"]] = \
                result["counts"].get(e["category"], 0) + 1

        # Score recalculate karo
        result["health_score"] = compute_health_score(result["classified"])

    return result
