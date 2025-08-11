#!/bin/bash
# Aktifkan virtual environment
source ./.venv/bin/activate

export $(grep -v '^#' .env | xargs)

# Jalankan uvicorn
exec uvicorn main:app --reload --host 0.0.0.0 --port $PORT