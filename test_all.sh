#!/bin/bash

# Function to run the python test script
run_tests() {
    echo "------------------------------------------------"
    python3 test_system.py
    echo "------------------------------------------------"
}

echo "OCR Project End-to-End Test Suite"

# 1. Test Local Execution
echo -e "\n--- STAGE 1: LOCAL TEST ---"
echo "Starting services locally with run_local.sh..."
./run_local.sh &
PID=$!
sleep 15 # Give time for models to load

run_tests

echo "Cleaning up local services..."
kill -SIGINT $PID
sleep 5

# 2. Test Docker Execution
echo -e "\n--- STAGE 2: DOCKER TEST ---"
echo "Building and starting containers..."
docker-compose up --build -d

echo "Waiting for Docker services to initialize (30s)..."
sleep 30

run_tests

echo "Shutting down Docker containers..."
docker-compose down

echo -e "\nEnd-to-End Testing Complete!"
