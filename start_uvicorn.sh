#!/bin/bash
# Aktifkan virtual environment
source ./.venv/bin/activate

# Jalankan uvicorn
exec uvicorn main:app --reload --host 0.0.0.0 --port 8118