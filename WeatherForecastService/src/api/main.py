"""FastAPI ASGI application for WeatherForecastService.

This module exposes the ASGI app object `app` used by uvicorn and other ASGI servers.

Usage:
- Start locally from the WeatherForecastService directory:
    uvicorn src.api.main:app --host 0.0.0.0 --port 3000 --reload
- Or use the convenience script which sets PYTHONPATH:
    bash ./run.sh

OpenAPI:
- Interactive docs: /docs
- OpenAPI JSON: /openapi.json

Notes:
- This service makes outbound calls to Nominatim (geocoding) and Open-Meteo (weather).
- If running in an environment without egress network access, requests may fail with 502,
  which is handled gracefully by the routes and tests.
"""
import os
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.api.utils import (
    get_clothing_recommendations_for_forecast,
    map_open_meteo_to_daily_forecast,
    mock_popular_places_for_city,
)

# Load environment variables if .env exists
load_dotenv()

# PUBLIC_INTERFACE
class DailyForecast(BaseModel):
    """Represents a single day's forecast with simplified fields."""
    date: str = Field(..., description="ISO date for the forecasted day (YYYY-MM-DD).")
    min_temp_c: float = Field(..., description="Minimum temperature in Celsius.")
    max_temp_c: float = Field(..., description="Maximum temperature in Celsius.")
    precipitation_probability: int = Field(..., ge=0, le=100, description="Chance of precipitation in percentage.")
    condition: str = Field(..., description="Simplified condition label such as 'Clear', 'Cloudy', 'Rain', 'Snow'.")


# PUBLIC_INTERFACE
class ClothingRecommendation(BaseModel):
    """Clothing suggestion for a given day."""
    date: str = Field(..., description="ISO date corresponding to the forecast day.")
    tips: List[str] = Field(..., description="List of clothing tips for the day's conditions.")


# PUBLIC_INTERFACE
class PopularPlace(BaseModel):
    """Represents a popular place to visit in the city."""
    name: str = Field(..., description="Place name.")
    description: str = Field(..., description="Short description.")
    category: str = Field(..., description="Type/category (e.g., 'Museum', 'Park').")


# PUBLIC_INTERFACE
class TravelGuideResponse(BaseModel):
    """Response model for the travel guide endpoint."""
    city: str = Field(..., description="Requested city name.")
    country: str = Field(..., description="Detected country name or code if available.")
    forecast_5day: List[DailyForecast] = Field(..., description="Five day daily forecast.")
    clothing_recommendations: List[ClothingRecommendation] = Field(..., description="Per-day clothing suggestions.")
    popular_places: List[PopularPlace] = Field(..., description="Popular places to visit in the city.")


app = FastAPI(
    title="WeatherForecastService",
    description=(
        "FastAPI service that converts a city name into a short travel guide including:\n"
        "- 5-day weather forecast (via Open-Meteo and Nominatim geocoding)\n"
        "- Clothing recommendations derived from the forecast\n"
        "- Popular places to visit (mocked sample data)\n\n"
        "Notes:\n"
        "- This service uses the Open-Meteo API (no API key required) for weather data.\n"
        "- It uses the OpenStreetMap Nominatim service (no key) for geocoding city to coordinates.\n"
        "- Popular places are mocked to keep setup minimal. You can replace with a real API later."
    ),
    version="1.0.0",
    contact={"name": "Travel Assistant", "url": "https://example.com"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "health", "description": "Service health and info"},
        {"name": "travel", "description": "City to travel guide"},
    ],
)

# CORS configuration - permissive for demo; adjust in production environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health check", description="Simple health-check endpoint.")
def health_check():
    """Health check endpoint that returns a basic status message."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/api/v1/travel-guide",
    response_model=TravelGuideResponse,
    tags=["travel"],
    summary="Get travel guide for a city",
    description=(
        "Provide a city name to receive:\n"
        "- A 5-day forecast (min/max temp, precip probability, condition)\n"
        "- Clothing recommendations derived from the forecast\n"
        "- A mocked list of popular places in the city\n\n"
        "Implementation details:\n"
        "1) City is geocoded to coordinates using Nominatim (no API key required).\n"
        "2) Weather is fetched from Open-Meteo daily forecast API.\n"
        "3) Clothing tips are generated from weather data.\n"
        "4) Popular places are currently mocked.\n\n"
        "TODO: Replace mocked places with a public POI API (e.g., Wikipedia, OpenTripMap) if desired."
    ),
    operation_id="getTravelGuideForCity",
)
async def get_travel_guide(city: str = Query(..., description="City name to search, e.g., 'Paris' or 'New York'")) -> TravelGuideResponse:
    """
    Retrieve a travel guide for a given city.

    Parameters:
        city: City name to geocode and fetch a 5-day forecast.

    Returns:
        TravelGuideResponse: Includes city/country, 5-day forecast, clothing recommendations, and popular places.

    Raises:
        HTTPException 404 if city not found.
        HTTPException 502 if an external dependency fails.
    """
    # 1) Geocode the city to get coordinates
    geocode = await _geocode_city(city)
    if not geocode:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found.")
    lat, lon = geocode["lat"], geocode["lon"]
    norm_city = geocode.get("display_name_city") or geocode.get("name") or city
    country = geocode.get("display_name_country") or geocode.get("address", {}).get("country_code", "").upper() or "Unknown"

    # 2) Fetch 5-day forecast from Open-Meteo
    daily_forecast = await _fetch_5day_forecast(lat, lon)

    # 3) Generate clothing recommendations
    clothing = get_clothing_recommendations_for_forecast(daily_forecast)

    # 4) Mock popular places
    places = mock_popular_places_for_city(norm_city, country)

    return TravelGuideResponse(
        city=norm_city,
        country=country,
        forecast_5day=daily_forecast,
        clothing_recommendations=clothing,
        popular_places=places,
    )


async def _geocode_city(city: str):
    """
    Geocode city name to coordinates using OpenStreetMap Nominatim API.
    No API key is required. We pick the first match.

    Returns a dict:
    {
        'lat': float,
        'lon': float,
        'name': str,
        'display_name_city': Optional[str],
        'display_name_country': Optional[str]
    }
    or None if not found.
    """
    # Nominatim usage policy requires a User-Agent or referer
    headers = {
        "User-Agent": os.getenv("GEOCODER_USER_AGENT", "WeatherForecastService/1.0 (demo)")
    }
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    url = "https://nominatim.openstreetmap.org/search"
    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                return None
            item = items[0]
            address = item.get("address", {})
            # Extract a readable city and country if present
            display_city = address.get("city") or address.get("town") or address.get("village") or item.get("display_name")
            display_country = address.get("country")
            return {
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "name": item.get("display_name"),
                "display_name_city": display_city,
                "display_name_country": display_country,
                "address": address,
            }
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Geocoding service error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="Geocoding service not reachable") from e
        except Exception as e:
            raise HTTPException(status_code=502, detail="Unexpected geocoding error") from e


async def _fetch_5day_forecast(lat: float, lon: float) -> List[DailyForecast]:
    """
    Fetch a 5-day daily forecast from Open-Meteo API (no API key required).
    We request min/max temperatures, precipitation probability, and weathercode.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto",
        "forecast_days": 5,
    }
    url = "https://api.open-meteo.com/v1/forecast"
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return map_open_meteo_to_daily_forecast(data)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Weather provider error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail="Weather provider not reachable") from e
        except Exception as e:
            raise HTTPException(status_code=502, detail="Unexpected weather provider error") from e
