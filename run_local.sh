#!/bin/bash

PROJECT_ROOT=$(pwd)
MODEL_PATH="$PROJECT_ROOT/model/ocr_model.pth"

# Export shared variables
export PYTHONPATH="$PROJECT_ROOT/classifier:$PYTHONPATH"
export MODEL_PATH="$MODEL_PATH"
export CHAR_URL="http://localhost:8001"
export WORD_URL="http://localhost:8002"




UVICORN_BIN=".venv/bin/uvicorn"
if [ ! -f "$UVICORN_BIN" ]; then
    UVICORN_BIN=$(which uvicorn)
fi

if [ -z "$UVICORN_BIN" ]; then
    echo "Error: uvicorn not found. Please install it or create a .venv"
    exit 1
fi

echo "Starting OCR System locally using $UVICORN_BIN..."

# Function to kill processes on script exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    pkill -f "$UVICORN_BIN"
    exit
}

# Trap CTRL+C to run cleanup
trap cleanup SIGINT

# 1. Start Character Service (Port 8001)
echo "[1/3] Starting Character Service on port 8001..."
"$UVICORN_BIN" main:app --app-dir classifier/character-classifier --host 0.0.0.0 --port 8001 > app.log 2>&1 &
sleep 5 # Wait for model loading

# 2. Start Word Service (Port 8002)
echo "[2/3] Starting Word Service on port 8002..."
"$UVICORN_BIN" main:app --app-dir classifier/word-classifier --host 0.0.0.0 --port 8002 >> app.log 2>&1 &
sleep 5 # Wait for EasyOCR loading

# 3. Start Gateway (Port 8000)
echo "[3/3] Starting Gateway on port 8000..."
"$UVICORN_BIN" gateway.main:app --host 0.0.0.0 --port 8000 >> app.log 2>&1 &

echo ""
echo "All services are running!"
echo "------------------------------------------------"
echo "Gateway URL:   http://localhost:8000"
echo "All logs are being consolidated into: app.log"
echo "Press CTRL+C to stop everything."
echo "------------------------------------------------"



# Keep the script running so we can capture CTRL+C
wait
