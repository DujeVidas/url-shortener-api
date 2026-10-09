#!/bin/sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

echo "Starting FastAPI..."
exec python -m app.run