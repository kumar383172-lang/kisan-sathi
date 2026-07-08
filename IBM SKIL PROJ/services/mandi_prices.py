"""
services/mandi_prices.py
─────────────────────────
Simulates fetching mandi (wholesale market) prices.
In production replace _fetch_agmarknet() with a real API call to
data.gov.in / eNAM / Agmarknet API endpoints.
"""

import logging
import random
from datetime import date

logger = logging.getLogger(__name__)

# Indicative price ranges (min, max) in Rs/quintal
PRICE_RANGES = {
    "Tomato":     (600, 2800),
    "Onion":      (400, 2200),
    "Potato":     (500, 1800),
    "Wheat":      (2100, 2600),
    "Rice":       (1800, 3500),
    "Maize":      (1700, 2400),
    "Cotton":     (5500, 7200),
    "Soybean":    (3800, 4800),
    "Chickpea":   (4500, 5800),
    "Mustard":    (4600, 5700),
    "Sugarcane":  (285, 360),   # Rs/quintal
    "Groundnut":  (4500, 6500),
}

MAJOR_MANDIS = [
    "Azadpur (Delhi)",
    "Vashi (Mumbai)",
    "Pune",
    "Nashik",
    "Indore",
    "Ahmedabad",
    "Nagpur",
    "Ludhiana",
    "Amritsar",
    "Bhopal",
]


def get_mandi_prices(crops: list[str] | None = None) -> list[dict]:
    """
    Return mandi price data for requested crops.
    Falls back to all tracked crops if none specified.
    """
    if not crops:
        crops = list(PRICE_RANGES.keys())

    today = date.today().strftime("%d %b %Y")
    prices = []
    for crop in crops:
        if crop not in PRICE_RANGES:
            continue
        lo, hi = PRICE_RANGES[crop]
        modal = random.randint(lo, hi)
        min_p = max(lo, modal - random.randint(50, 200))
        max_p = min(hi, modal + random.randint(50, 200))
        mandi = random.choice(MAJOR_MANDIS)
        trend = random.choice(["↑ Rising", "↓ Falling", "→ Stable"])
        prices.append({
            "crop": crop,
            "modal_price": modal,
            "min_price": min_p,
            "max_price": max_p,
            "mandi": mandi,
            "unit": "Rs/Quintal",
            "trend": trend,
            "date": today,
        })
    return prices


def prices_to_text(prices: list[dict]) -> str:
    """Format price data as a RAG context text snippet."""
    lines = ["Today's Mandi Prices:"]
    for p in prices:
        lines.append(
            f"  • {p['crop']}: Modal Rs {p['modal_price']}/qtl "
            f"(Min {p['min_price']} – Max {p['max_price']}) at {p['mandi']} {p['trend']}"
        )
    return "\n".join(lines)
