#!/usr/bin/env bash
# Convenience launcher for WeatherForecastService
# - Ensures we are in the service directory
# - Sets PYTHONPATH so `src.api.*` imports resolve
# - Starts uvicorn on port 3000

set -euo pipefail

# Move to the directory containing this script
cd "$(dirname "${BASH_SOURCE[0]}")"

# Set PYTHONPATH to current dir to allow `from src.api...`
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

# Default host/port; can be overridden by environment
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3000}"

echo "Starting WeatherForecastService on http://${HOST}:${PORT} ..."
exec uvicorn src.api.main:app --host "${HOST}" --port "${PORT}" --reload
