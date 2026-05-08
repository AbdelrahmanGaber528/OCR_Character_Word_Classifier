#!/bin/bash

# =========================================================
# OCR Microservices Local Runner
# =========================================================

set -m

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
MODEL_PATH="$PROJECT_ROOT/model/ocr_model.pth"

# =========================================================
# Environment Variables
# =========================================================

export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/classifier:$PYTHONPATH"
export MODEL_PATH="$MODEL_PATH"

export CHAR_URL="http://127.0.0.1:8001"
export WORD_URL="http://127.0.0.1:8002"

# =========================================================
# Uvicorn Detection
# =========================================================

UVICORN_BIN="$PROJECT_ROOT/.venv/bin/uvicorn"

if [ ! -f "$UVICORN_BIN" ]; then
    UVICORN_BIN=$(which uvicorn)
fi

if [ -z "$UVICORN_BIN" ]; then
    echo "ERROR: uvicorn not found."
    echo "Activate your virtual environment first."
    exit 1
fi

# =========================================================
# Logs
# =========================================================

LOG_FILE="$PROJECT_ROOT/app.log"

rm -f "$LOG_FILE"
touch "$LOG_FILE"

# =========================================================
# Cleanup Function
# =========================================================

cleanup() {
    echo ""
    echo "================================================="
    echo "Stopping OCR services..."
    echo "================================================="

    [ ! -z "$CHAR_PID" ] && kill "$CHAR_PID" 2>/dev/null
    [ ! -z "$WORD_PID" ] && kill "$WORD_PID" 2>/dev/null
    [ ! -z "$GATEWAY_PID" ] && kill "$GATEWAY_PID" 2>/dev/null

    sleep 2

    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# =========================================================
# Helper Function
# =========================================================

start_service() {
    SERVICE_NAME=$1
    APP_DIR=$2
    APP_TARGET=$3
    PORT=$4

    echo ""
    echo "================================================="
    echo "Starting $SERVICE_NAME on port $PORT..."
    echo "================================================="

    "$UVICORN_BIN" "$APP_TARGET" \
        --app-dir "$APP_DIR" \
        --host 0.0.0.0 \
        --port "$PORT" \
        >> "$LOG_FILE" 2>&1 &

    PID=$!

    sleep 5

    if ps -p $PID > /dev/null; then
        echo "$SERVICE_NAME started successfully (PID: $PID)"
    else
        echo "ERROR: $SERVICE_NAME failed to start."
        echo ""
        echo "Last logs:"
        echo "-------------------------------------------------"
        tail -n 50 "$LOG_FILE"
        echo "-------------------------------------------------"
        cleanup
    fi

    echo $PID
}

# =========================================================
# Start Services
# =========================================================

echo ""
echo "================================================="
echo "Starting OCR System..."
echo "Project Root: $PROJECT_ROOT"
echo "Logs: $LOG_FILE"
echo "================================================="

# Character Service
CHAR_PID=$(start_service \
    "Character Service" \
    "$PROJECT_ROOT/classifier/character-classifier" \
    "main:app" \
    8001)

# Word Service
WORD_PID=$(start_service \
    "Word Service" \
    "$PROJECT_ROOT/classifier/word-classifier" \
    "main:app" \
    8002)

# Gateway Service
GATEWAY_PID=$(start_service \
    "Gateway Service" \
    "$PROJECT_ROOT" \
    "gateway.main:app" \
    8000)

# =========================================================
# Final Status
# =========================================================

echo ""
echo "================================================="
echo "OCR SYSTEM IS RUNNING"
echo "================================================="
echo "Gateway    : http://127.0.0.1:8000"
echo "Character  : http://127.0.0.1:8001"
echo "Word       : http://127.0.0.1:8002"
echo ""
echo "Logs:"
echo "tail -f $LOG_FILE"
echo ""
echo "Press CTRL+C to stop all services."
echo "================================================="

# =========================================================
# Keep Script Alive
# =========================================================

wait
