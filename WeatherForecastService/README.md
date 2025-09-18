# WeatherForecastService

FastAPI service that takes a city as input and returns:
- 5-day weather forecast
- Clothing recommendations
- Popular places to visit (mocked for simplicity)

Uses:
- Geocoding: OpenStreetMap Nominatim (no API key required)
- Weather: Open-Meteo (no API key required)

## Features

- Clean route and service separation
- Graceful error handling (city not found, upstream error)
- OpenAPI documentation with Pydantic response models
- Test suite with pytest
- CORS enabled for quick front-end prototyping

## Quickstart

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the service (ensure your working directory is WeatherForecastService/):

```bash
# Option A: using uvicorn directly
uvicorn src.api.main:app --host 0.0.0.0 --port 3000 --reload

# Option B: convenience script (sets PYTHONPATH and starts uvicorn on port 3000)
bash ./run.sh
```

4. Open your browser at:
- Swagger UI: http://localhost:3000/docs
- Health: http://localhost:3000/

Example request:
```
GET /api/v1/travel-guide?city=Paris
```

If you previously saw an error like `Could not import module "main"`, it was due to running `uvicorn main:app` from the wrong directory. Always target `src.api.main:app` and run from the `WeatherForecastService/` directory so imports like `from src.api...` resolve correctly.

## Environment Variables

Create an optional `.env` file in `WeatherForecastService/` if you want to customize:
- `ALLOWED_ORIGINS` — CORS origins (default: `*`)
- `GEOCODER_USER_AGENT` — User-Agent header used for Nominatim requests (default: `WeatherForecastService/1.0 (demo)`)

Do not commit real secrets. No API keys are required for the default setup.

## Notes and TODOs

- Popular places are currently mocked. Replace with a real POI API later (e.g., OpenTripMap, Wikipedia).
- Add caching (e.g., in-memory TTL) to reduce repeated calls to geocoding and weather providers if needed.
- Add more detailed weather insights (wind, UV, hourly breakdown) as needed.

## Tests

Run tests:

```bash
pytest -q
```

Note: In CI environments without network access, tests will still pass basic schema validations and allow 502/404 outcomes from the external calls.

## Project Structure

```
WeatherForecastService/
  ├─ src/
  │   └─ api/
  │       ├─ __init__.py
  │       ├─ main.py                # FastAPI app, routes, models
  │       ├─ utils.py               # Mapping, recommendations, mock places
  │       └─ schemas.py             # Re-exported schemas
  ├─ requirements.txt
  ├─ README.md
  ├─ run.sh                         # Convenience launcher on port 3000
  └─ test_main.py
```

## OpenAPI Export

To export the OpenAPI schema file:

```bash
python -m src.api.generate_openapi
```

The schema will be saved at: `interfaces/openapi.json`.
