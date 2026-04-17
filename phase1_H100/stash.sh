#!/bin/bash
# Start script for Phase 1 FastAPI worker

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting Phase 1 API on port 8001 (listening on 0.0.0.0)..."
python3 main.py