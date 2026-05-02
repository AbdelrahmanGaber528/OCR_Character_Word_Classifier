# Distributed OCR System

A microservices-based Optical Character Recognition (OCR) system that provides both single-character classification and full-word recognition. The system is designed with a Gateway pattern and a centralized logging service.

## Architecture

The project is split into four main services:

1.  **Gateway (Port 8000):** The entry point. Routes requests to the appropriate classification service and serves a simple web UI.
2.  **Character Service (Port 8001):** Uses a custom MobileNetV2 (or OCR_CNN) model trained on handwritten/printed characters to predict single letters.
3.  **Word Service (Port 8002):** Uses EasyOCR to perform text detection and recognition on full images/words.
4.  **Logger Service (Port 8003):** A centralized logging hub that collects logs from all services and saves them to `app.log`.

## Tech Stack

*   **Language:** Python 3.11+
*   **Framework:** FastAPI, Uvicorn
*   **Deep Learning:** PyTorch, Torchvision, EasyOCR
*   **Containerization:** Docker, Docker Compose
*   **Imaging:** Pillow, OpenCV

## Getting Started

### Prerequisites

*   Python 3.11 or higher
*   Docker and Docker Compose (optional, for containerized run)
*   A virtual environment is recommended: `python3 -m venv .venv && source .venv/bin/activate`

### Installation

1.  Clone the repository.
2.  Install dependencies for all services:
    ```bash
    pip install -r gateway/requirements.txt
    pip install -r classifier/character-classifier/requirements.txt
    pip install -r classifier/word-classifier/requirements.txt
    pip install -r logger/requirements.txt
    ```

## Running the Project

### Option 1: Local Execution (Fastest for Development)

I have provided an automation script that sets up the environment and starts all services in the background.

```bash
chmod +x run_local.sh
./run_local.sh
```
*   Logs from all services will be consolidated into a single `app.log` file in the root directory.
*   Press `CTRL+C` to stop all services.

### Option 2: Docker Compose

To run the entire stack in isolated containers:

```bash
docker-compose up --build
```
The Gateway will be available at `http://localhost:8000`.

## API Documentation

Each service provides interactive Swagger UI (OpenAPI) documentation for exploring and testing endpoints:

*   **Gateway:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Character Service:** [http://localhost:8001/docs](http://localhost:8001/docs)
*   **Word Service:** [http://localhost:8002/docs](http://localhost:8002/docs)
*   **Logger Service:** [http://localhost:8003/docs](http://localhost:8003/docs)

## API Usage

### Gateway Endpoints
*   `GET /`: Web interface for uploading images.
*   `POST /predict/character`: Upload an image to predict a single character.
*   `POST /predict/word`: Upload an image to recognize a full word.

### Direct Service Access
*   `GET http://localhost:8001/health`: Character Service health check.
*   `GET http://localhost:8002/health`: Word Service health check.
*   `GET http://localhost:8003/docs`: Interactive Swagger UI for the Logger.

## Testing

A comprehensive test suite is included to verify the system's integrity.

1.  **System Verification:** Test all running services and OCR accuracy.
    ```bash
    python3 test_system.py
    ```
2.  **End-to-End Suite:** Automatically tests the project in both Local and Docker modes.
    ```bash
    ./test_all.sh
    ```

## Project Structure

```text
.
├── classifier/
│   ├── character-classifier/  # Custom model service
│   ├── word-classifier/       # EasyOCR service
│   └── shared/                # Shared logic (preprocessing, model loading)
├── gateway/                   # API Gateway & Web UI
├── logger/                    # Centralized logging service
├── model/                     # Trained .pth model files
├── tested_photos/             # Sample images for testing
├── docker-compose.yml         # Container orchestration
└── run_local.sh               # Local automation script
```

## License

This project is for educational purposes as part of an Advanced Machine Learning curriculum.
