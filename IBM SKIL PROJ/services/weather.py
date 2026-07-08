"""
services/weather.py
────────────────────
Fetches real-time weather data from the free Open-Meteo API.
No API key required.
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Icy Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌦️"),
    55: ("Dense Drizzle", "🌧️"),
    61: ("Slight Rain", "🌧️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Light Snow", "❄️"),
    73: ("Moderate Snow", "❄️"),
    75: ("Heavy Snow", "❄️"),
    80: ("Rain Showers", "🌦️"),
    81: ("Heavy Showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"),
    99: ("Severe Thunderstorm", "⛈️"),
}


def get_weather(lat: float = 20.59, lon: float = 78.96) -> dict:
    """Fetch current weather + 7-day forecast for the given coordinates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "soil_temperature_0cm",
            "soil_moisture_0_to_1cm",
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return _parse_weather(data)
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return _fallback_weather()


def _parse_weather(data: dict) -> dict:
    cur = data.get("current", {})
    daily = data.get("daily", {})

    wcode = cur.get("weather_code", 0)
    desc, icon = WMO_CODES.get(wcode, ("Unknown", "🌡️"))

    forecast = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates[:7]):
        dc = daily.get("weather_code", [0] * 7)[i]
        d_desc, d_icon = WMO_CODES.get(dc, ("Clear", "☀️"))
        forecast.append({
            "date": date,
            "description": d_desc,
            "icon": d_icon,
            "temp_max": daily.get("temperature_2m_max", ["-"] * 7)[i],
            "temp_min": daily.get("temperature_2m_min", ["-"] * 7)[i],
            "precipitation": daily.get("precipitation_sum", [0] * 7)[i],
        })

    return {
        "temperature": cur.get("temperature_2m", "--"),
        "feels_like": cur.get("apparent_temperature", "--"),
        "humidity": cur.get("relative_humidity_2m", "--"),
        "precipitation": cur.get("precipitation", 0),
        "wind_speed": cur.get("wind_speed_10m", "--"),
        "weather_desc": desc,
        "weather_icon": icon,
        "soil_temp": cur.get("soil_temperature_0cm", "--"),
        "soil_moisture": round(cur.get("soil_moisture_0_to_1cm", 0) * 100, 1),
        "forecast": forecast,
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


def _fallback_weather() -> dict:
    return {
        "temperature": "--",
        "feels_like": "--",
        "humidity": "--",
        "precipitation": 0,
        "wind_speed": "--",
        "weather_desc": "Unavailable",
        "weather_icon": "❓",
        "soil_temp": "--",
        "soil_moisture": "--",
        "forecast": [],
        "updated_at": "Could not fetch",
    }


def weather_to_text(w: dict) -> str:
    """Convert weather dict to a text snippet for RAG context injection."""
    return (
        f"Current weather: {w['weather_desc']}, Temperature {w['temperature']}°C "
        f"(feels like {w['feels_like']}°C), Humidity {w['humidity']}%, "
        f"Wind {w['wind_speed']} km/h, Precipitation {w['precipitation']} mm today, "
        f"Soil temp {w['soil_temp']}°C, Soil moisture {w['soil_moisture']}%."
    )
