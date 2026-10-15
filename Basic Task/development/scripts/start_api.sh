#!/bin/bash

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"

cd "$ROOT_DIR"

source "$PROJECT_ROOT/.venv/bin/activate"

echo "Starting FastAPI..."
echo "Using python: $(which python)"

python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000
