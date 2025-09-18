import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("message") == "Healthy"


@pytest.mark.parametrize("city", ["Paris", "New York", "Tokyo"])
def test_travel_guide_schema(city):
    r = client.get("/api/v1/travel-guide", params={"city": city})
    # We don't assert 200 because network may be restricted in CI.
    # If network blocked, FastAPI should return 502 due to our error handling.
    assert r.status_code in (200, 404, 502)

    if r.status_code == 200:
        data = r.json()
        assert set(data.keys()) == {"city", "country", "forecast_5day", "clothing_recommendations", "popular_places"}
        assert isinstance(data["forecast_5day"], list) and len(data["forecast_5day"]) >= 1
        assert isinstance(data["clothing_recommendations"], list) and len(data["clothing_recommendations"]) >= 1
        assert isinstance(data["popular_places"], list) and len(data["popular_places"]) >= 1
