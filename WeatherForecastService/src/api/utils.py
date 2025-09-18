from typing import Dict, List

from src.api.main import DailyForecast, ClothingRecommendation, PopularPlace


def _weathercode_to_condition(code: int) -> str:
    """
    Simplified mapping from Open-Meteo weather codes to common labels.
    Reference: https://open-meteo.com/en/docs
    """
    rain_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    snow_codes = {71, 73, 75, 85, 86}
    thunder_codes = {95, 96, 99}
    fog_codes = {45, 48}
    drizzle_codes = {51, 53, 55, 56, 57}
    if code == 0:
        return "Clear"
    if code in {1, 2, 3}:
        return "Cloudy"
    if code in fog_codes:
        return "Fog"
    if code in drizzle_codes:
        return "Drizzle"
    if code in rain_codes:
        return "Rain"
    if code in snow_codes:
        return "Snow"
    if code in thunder_codes:
        return "Thunderstorm"
    return "Unknown"


def map_open_meteo_to_daily_forecast(data: Dict) -> List[DailyForecast]:
    """
    Convert Open-Meteo 'daily' response to List[DailyForecast]
    """
    daily = data.get("daily", {})
    dates = daily.get("time", []) or []
    tmin = daily.get("temperature_2m_min", []) or []
    tmax = daily.get("temperature_2m_max", []) or []
    precip_prob = daily.get("precipitation_probability_max", []) or []
    weathercodes = daily.get("weathercode", []) or []

    out: List[DailyForecast] = []
    for i in range(min(len(dates), 5)):
        date = dates[i]
        min_temp = float(tmin[i]) if i < len(tmin) else 0.0
        max_temp = float(tmax[i]) if i < len(tmax) else 0.0
        precip = int(precip_prob[i]) if i < len(precip_prob) and precip_prob[i] is not None else 0
        wcode = int(weathercodes[i]) if i < len(weathercodes) and weathercodes[i] is not None else -1
        condition = _weathercode_to_condition(wcode)
        out.append(
            DailyForecast(
                date=date,
                min_temp_c=min_temp,
                max_temp_c=max_temp,
                precipitation_probability=precip,
                condition=condition,
            )
        )
    return out


def _clothing_tips_for_day(day: DailyForecast) -> List[str]:
    """
    Rule-based tips from a single day's forecast.
    """
    tips: List[str] = []
    # Temperature-based
    if day.max_temp_c >= 28:
        tips.append("Wear light, breathable clothing")
        tips.append("Use sunscreen and stay hydrated")
    elif day.max_temp_c >= 22:
        tips.append("T-shirt or light layers recommended")
    elif day.max_temp_c >= 12:
        tips.append("Consider a light jacket or sweater")
    else:
        tips.append("Wear a warm jacket and layers")
        tips.append("Consider hat and gloves if windy")

    # Precipitation-based
    if day.precipitation_probability >= 60:
        tips.append("Bring an umbrella or raincoat")
        tips.append("Waterproof footwear suggested")
    elif day.precipitation_probability >= 30:
        tips.append("Pack a compact umbrella just in case")

    # Condition-based augmentation
    if day.condition in {"Snow"}:
        tips.append("Wear insulated boots for snow")
    if day.condition in {"Fog"}:
        tips.append("Plan for low visibility; reflective clothing helps")
    if day.condition in {"Thunderstorm"}:
        tips.append("Avoid outdoor activities during storms")

    # De-duplicate while preserving order
    seen = set()
    unique_tips = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            unique_tips.append(t)
    return unique_tips


def get_clothing_recommendations_for_forecast(forecast: List[DailyForecast]) -> List[ClothingRecommendation]:
    """
    Generate per-day clothing recommendations given a list of daily forecasts.
    """
    recs: List[ClothingRecommendation] = []
    for day in forecast:
        recs.append(
            ClothingRecommendation(
                date=day.date,
                tips=_clothing_tips_for_day(day),
            )
        )
    return recs


def mock_popular_places_for_city(city: str, country: str) -> List[PopularPlace]:
    """
    Return a mocked set of popular places for a given city.
    TODO: Replace with a real data source (e.g., OpenTripMap, Wikipedia, Triposo) when keys and setup are available.
    """
    samples: Dict[str, List[Dict[str, str]]] = {
        "paris": [
            {"name": "Eiffel Tower", "description": "Iconic wrought-iron lattice tower.", "category": "Landmark"},
            {"name": "Louvre Museum", "description": "World's largest art museum.", "category": "Museum"},
            {"name": "Notre-Dame Cathedral", "description": "Famous medieval Catholic cathedral.", "category": "Cathedral"},
        ],
        "new york": [
            {"name": "Central Park", "description": "Urban park in Manhattan.", "category": "Park"},
            {"name": "Statue of Liberty", "description": "Colossal neoclassical sculpture on Liberty Island.", "category": "Landmark"},
            {"name": "Metropolitan Museum of Art", "description": "Vast collection of art from around the world.", "category": "Museum"},
        ],
        "tokyo": [
            {"name": "Senso-ji", "description": "Ancient Buddhist temple in Asakusa.", "category": "Temple"},
            {"name": "Shinjuku Gyoen", "description": "Large park with traditional gardens.", "category": "Park"},
            {"name": "Tokyo Skytree", "description": "Broadcasting and observation tower.", "category": "Landmark"},
        ],
    }
    key = city.strip().lower()
    places = samples.get(key)
    if not places:
        # Provide a generic default
        places = [
            {"name": f"City Museum of {city}", "description": "Local museum highlighting the city's history.", "category": "Museum"},
            {"name": f"Central Park of {city}", "description": "Green space popular among locals and tourists.", "category": "Park"},
            {"name": f"Old Town {city}", "description": "Historic district with cafes and boutiques.", "category": "Historic"},
        ]
    return [PopularPlace(**p) for p in places]
