"""
services/crop_advisor.py
─────────────────────────
Rule-based crop recommendation engine used to supplement the LLM.
Returns crop suggestions based on season, soil type, and state.
"""

from datetime import date

KHARIF_CROPS = {
    "Black (Vertisol)": ["Cotton", "Soybean", "Sorghum (Jowar)", "Pigeonpea (Tur)", "Maize"],
    "Alluvial":         ["Rice", "Maize", "Sugarcane", "Groundnut", "Jute"],
    "Red Laterite":     ["Groundnut", "Finger Millet (Ragi)", "Castor", "Maize", "Blackgram"],
    "Sandy Loam":       ["Bajra (Pearl Millet)", "Moong", "Sesame (Til)", "Cowpea", "Watermelon"],
    "Sandy":            ["Bajra", "Groundnut", "Cowpea", "Cluster Bean", "Sesame"],
    "Loamy":            ["Rice", "Maize", "Cotton", "Soybean", "Groundnut"],
}

RABI_CROPS = {
    "Black (Vertisol)": ["Chickpea (Chana)", "Wheat", "Linseed", "Safflower", "Sunflower"],
    "Alluvial":         ["Wheat", "Mustard", "Barley", "Pea", "Potato"],
    "Red Laterite":     ["Chickpea", "Lentil", "Mustard", "Wheat", "Sunflower"],
    "Sandy Loam":       ["Mustard", "Wheat", "Barley", "Chickpea", "Fenugreek"],
    "Sandy":            ["Mustard", "Barley", "Chickpea", "Coriander"],
    "Loamy":            ["Wheat", "Mustard", "Potato", "Onion", "Tomato"],
}

ZAID_CROPS = {
    "_all_": ["Watermelon", "Muskmelon", "Cucumber", "Summer Squash", "Moong", "Groundnut"]
}


def get_season() -> str:
    """Determine current Indian agricultural season."""
    month = date.today().month
    if 6 <= month <= 9:
        return "Kharif"
    elif month >= 10 or month <= 2:
        return "Rabi"
    else:
        return "Zaid"


def recommend_crops(soil_type: str = "Loamy", season: str | None = None) -> dict:
    """Return crop recommendations for given soil type and season."""
    season = season or get_season()
    soil_key = _match_soil(soil_type)

    if season == "Kharif":
        crops = KHARIF_CROPS.get(soil_key, KHARIF_CROPS["Loamy"])
    elif season == "Rabi":
        crops = RABI_CROPS.get(soil_key, RABI_CROPS["Loamy"])
    else:
        crops = ZAID_CROPS["_all_"]

    return {
        "season": season,
        "soil_type": soil_key,
        "recommended_crops": crops,
        "tips": _season_tips(season),
    }


def _match_soil(soil: str) -> str:
    soil_lower = soil.lower()
    if "black" in soil_lower or "cotton" in soil_lower or "vertisol" in soil_lower:
        return "Black (Vertisol)"
    elif "alluvial" in soil_lower:
        return "Alluvial"
    elif "red" in soil_lower or "laterite" in soil_lower:
        return "Red Laterite"
    elif "sandy loam" in soil_lower:
        return "Sandy Loam"
    elif "sandy" in soil_lower:
        return "Sandy"
    else:
        return "Loamy"


def _season_tips(season: str) -> list[str]:
    tips = {
        "Kharif": [
            "Prepare field before onset of monsoon (May–June).",
            "Test soil pH; adjust if below 5.5 or above 8.0.",
            "Use certified disease-resistant seeds.",
            "Install weather-based pest monitoring traps.",
        ],
        "Rabi": [
            "Sow after soil temperature drops below 25°C.",
            "Ensure adequate moisture at sowing with pre-sowing irrigation.",
            "Apply phosphorus fertiliser at sowing time.",
            "Monitor wheat for yellow rust in December–January.",
        ],
        "Zaid": [
            "Use sprinkler/drip to cope with summer heat stress.",
            "Mulch soil to conserve moisture.",
            "Harvest early morning to reduce post-harvest losses.",
        ],
    }
    return tips.get(season, [])
