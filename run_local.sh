#!/bin/bash

# Configuration
PROJECT_ROOT=$(pwd)
MODEL_PATH="$PROJECT_ROOT/model/ocr_model.pth"
LOGGER_URL="http://localhost:8003/log"

# Export shared variables
export PYTHONPATH="$PROJECT_ROOT/classifier:$PYTHONPATH"
export MODEL_PATH="$MODEL_PATH"
export LOGGER_URL="$LOGGER_URL"
export CHAR_URL="http://localhost:8001"
export WORD_URL="http://localhost:8002"

echo "Starting OCR System locally..."

# Function to kill processes on script exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    pkill -f "uvicorn"
    exit
}

# Trap CTRL+C to run cleanup
trap cleanup SIGINT

# 1. Start Logger (Port 8003)
echo "[1/4] Starting Logger Service on port 8003..."
uvicorn logger.main:app --host 0.0.0.0 --port 8003 > logger.log 2>&1 &
sleep 2

# 2. Start Character Service (Port 8001)
echo "[2/4] Starting Character Service on port 8001..."
uvicorn main:app --app-dir classifier/character-classifier --host 0.0.0.0 --port 8001 > character_service.log 2>&1 &
sleep 5 # Wait for model loading

# 3. Start Word Service (Port 8002)
echo "[3/4] Starting Word Service on port 8002..."
uvicorn main:app --app-dir classifier/word-classifier --host 0.0.0.0 --port 8002 > word_service.log 2>&1 &
sleep 5 # Wait for EasyOCR loading

# 4. Start Gateway (Port 8000)
echo "[4/4] Starting Gateway on port 8000..."
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 > gateway.log 2>&1 &

echo ""
echo "All services are running!"
echo "------------------------------------------------"
echo "Gateway URL:   http://localhost:8000"
echo "Logger URL:    http://localhost:8003"
echo "Logs are being saved to *.log files in this directory."
echo "Press CTRL+C to stop everything."
echo "------------------------------------------------"

# Keep the script running so we can capture CTRL+C
wait
