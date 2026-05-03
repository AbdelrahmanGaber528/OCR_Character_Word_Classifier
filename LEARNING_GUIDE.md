# OCR Microservices System: Comprehensive Learning Guide

This document is a complete guide to understanding the Optical Character Recognition (OCR) project. It explains the architecture, breaks down the code line-by-line, and discusses cloud best practices and core software engineering concepts.

---

## Table of Contents
1.  [Core Concepts: The "Why"](#1-core-concepts-the-why)
2.  [System Architecture Overview](#2-system-architecture-overview)
3.  [Deep Dive: Code Walkthrough](#3-deep-dive-code-walkthrough)
    *   [Gateway Service (`gateway/main.py`)](#gateway-service)
    *   [Character Service (`classifier/character-classifier/main.py`)](#character-service)
    *   [Word Service (`classifier/word-classifier/main.py`)](#word-service)
    *   [Docker Compose (`docker-compose.yml`)](#docker-compose)
4.  [Best Practices & Cloud Readiness](#4-best-practices--cloud-readiness)
5.  [The Next Step: RabbitMQ (Asynchronous Messaging)](#5-the-next-step-rabbitmq-asynchronous-messaging)

---

## 1. Core Concepts: The "Why"

### What is a Microservice Architecture?
Instead of building one massive application (a "Monolith") that handles the UI, image processing, character recognition, and word recognition all together, we break it down into tiny, specialized "services."
*   **Why?** If the "Word Recognition" part requires heavy GPU resources, you can run it on an expensive server. If the "Gateway" just routes web traffic, it can run on a cheap, small server. If one service crashes, the others stay alive.

### What is an API Gateway?
The Gateway is the front door to your system. The user's browser only knows about `localhost:8000` (the Gateway).
*   **Why?** It hides the complexity of your system. The user doesn't need to know that Character processing lives on port 8001 and Word processing on 8002. The Gateway securely proxies (forwards) the requests to the right place.

### REST vs. RPC (Current vs. Future)
*   **Current (REST/HTTP):** The Gateway sends a request to the Character Service and *waits* for the response. This is simple but can cause the Gateway to freeze if the Character Service is slow.
*   **Future (RabbitMQ/Message Queue):** The Gateway drops a message in a queue ("Please process this image") and immediately tells the user "I'm working on it." The service picks it up when ready. This is called asynchronous processing.

---

## 2. System Architecture Overview

Currently, the system consists of three main Python (FastAPI) applications running in parallel:

1.  **Gateway (`gateway/`):** Exposes `/predict/character` and `/predict/word` to the outside world.
2.  **Character Classifier (`classifier/character-classifier/`):** Loads a custom PyTorch model (`ocr_model.pth`) to predict single letters.
3.  **Word Classifier (`classifier/word-classifier/`):** Loads the `easyocr` library to extract full words and sentences from images.

---

## 3. Deep Dive: Code Walkthrough

### Gateway Service
**File:** `gateway/main.py`
**Purpose:** Handle user uploads and forward them to the correct internal service.

```python
import os
import logging
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx # A library for making HTTP requests (like 'requests' but supports async)

# 1. Standard Logging Setup: Prints logs to the console in a clean format.
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("gateway")

# 2. Environment Variables: The Gateway needs to know where the other services live.
# In Docker, 'character_service' resolves to the IP address of that container.
CHAR_URL = os.getenv("CHAR_URL", "http://character_service:8001")
WORD_URL = os.getenv("WORD_URL", "http://word_service:8002")
TIMEOUT  = 30.0

app = FastAPI(title="OCR Gateway")

# ... (UI Setup omitted for brevity) ...

# 3. The Proxy Endpoint
@app.post("/predict/character")
async def predict_character(file: UploadFile = File(...)):
    # Security: Ensure the user actually uploaded an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be an image file.")

    logger.info(f"Proxying character request: {file.filename}")
    data = await file.read() # Read the image bytes into memory

    # 4. Make an Async HTTP Request to the Internal Service
    # We use 'async with' so the Gateway doesn't block other users while waiting.
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Forward the image to the Character Service
            resp = await client.post(
                f"{CHAR_URL}/predict-character",
                files={"file": (file.filename, data, file.content_type)},
            )
            resp.raise_for_status() # Throw an error if status is not 200 OK
            res = resp.json()       # Parse the JSON response
            logger.info(f"Character prediction success for {file.filename}")
            return res              # Return the result back to the user
        except httpx.TimeoutException:
            # Error Handling: Crucial in microservices. If the backend is down, tell the user gracefully.
            logger.error(f"Character service timed out for {file.filename}")
            raise HTTPException(504, "Character service timed out.")
        # ... (Other exception handling) ...
```

### Character Service
**File:** `classifier/character-classifier/main.py`
**Purpose:** Receive an image, run it through the PyTorch model, and return the predicted letter.

```python
import os
import logging
from contextlib import asynccontextmanager

import torch
import torch.nn.functional as F
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

from shared.model_loader import load_model
from shared.preprocessing import preprocess_image

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model/ocr_model.pth")
DEVICE     = os.getenv("DEVICE", "cpu") # Run on CPU or GPU

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("character-service")

ml: dict = {} # A global dictionary to hold our loaded model in memory

# 1. Lifespan (Startup/Shutdown):
# Machine Learning models take time to load from disk into memory (RAM/VRAM).
# We MUST do this only ONCE when the server starts, not on every user request.
@asynccontextmanager
async def lifespan(app: FastAPI): 
    logger.info(f"Loading model from {MODEL_PATH} ...")
    # Load the model weights (.pth file) into PyTorch
    model, class_names, model_name = load_model(MODEL_PATH, device=DEVICE)
    # Store them in the global dictionary
    ml.update(model=model, class_names=class_names, model_name=model_name)
    logger.info(f"Ready — {model_name} | {len(class_names)} classes | {DEVICE}")
    yield # The app runs here
    ml.clear() # Cleanup on shutdown

app = FastAPI(title="Character Service", lifespan=lifespan)

# ... (Pydantic schemas omitted) ...

# 2. Inference Function
@torch.no_grad() # Tell PyTorch not to calculate gradients (saves memory during prediction)
def _run(image_bytes: bytes, k: int = 3) -> CharResponse:
    # Convert raw bytes into a PyTorch Tensor (numbers)
    tensor = preprocess_image(image_bytes, ml["model_name"]).to(DEVICE)

    # Pass the tensor through the neural network
    logits = ml["model"](tensor)
    
    # Convert raw output (logits) into probabilities (percentages 0-1)
    probs  = F.softmax(logits, dim=1).squeeze()

    # Get the top 'k' highest probabilities
    top_probs, top_indices = torch.topk(probs, k=min(k, len(ml["class_names"])))

    # Map the indices back to actual letters (e.g., index 0 -> 'A')
    predictions = [
        Prediction(
            label=ml["class_names"][idx.item()],
            confidence=round(prob.item(), 4)
        )
        for prob, idx in zip(top_probs, top_indices)
    ]

    return CharResponse(...)

# 3. The Endpoint
@app.post("/predict-character", response_model=CharResponse)
async def predict_character(file: UploadFile = File(...)):
    # Note: This endpoint is only called by the Gateway, not the user directly.
    data = await file.read()
    try:
        res = _run(data, k=3)
        return res
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(500, str(e))
```

### Word Service
**File:** `classifier/word-classifier/main.py`
**Purpose:** Use EasyOCR to detect and read full text from images.

*Concepts are nearly identical to the Character Service (Lifespan loading, exposing a POST endpoint).*
**Key Difference:** It relies on the third-party `easyocr` library instead of a custom `.pth` PyTorch model. It expects full RGB images and returns a list of detected words and their bounding boxes.

### Docker Compose
**File:** `docker-compose.yml`
**Purpose:** Define how the microservices run together in isolated containers.

```yaml
services:
  gateway:
    build:
      context: . # Build from the current directory
      dockerfile: gateway/Dockerfile
    ports:
      - "8000:8000" # Expose port 8000 to your host machine
    depends_on:
      - character_service # Ensure backend starts before gateway
      - word_service
    environment:
      # Inject the internal Docker network URLs
      - CHAR_URL=http://character_service:8001
      - WORD_URL=http://word_service:8002

  character_service:
    build:
      context: .
      dockerfile: classifier/character-classifier/Dockerfile
    ports:
      - "8001:8001"
    volumes:
      # Mount the model folder from your hard drive into the container
      # This prevents having to copy a 100MB+ file into every Docker image
      - ./model:/app/model 
    environment:
      - MODEL_PATH=/app/model/ocr_model.pth

  # ... (word_service is similar) ...
```

---

## 4. Best Practices & Cloud Readiness

What makes this project "good" for deploying to AWS, GCP, or Azure?

1.  **Stateless Services:** None of your FastAPI apps save data to a local database or local disk (other than reading the model). If a container dies, you spin up a new one, and it works perfectly. This is rule #1 for Cloud Scalability.
2.  **Environment Variables (`os.getenv`):** You don't hardcode IP addresses (`localhost`). You use variables (`CHAR_URL`). In the cloud, the infrastructure injects these URLs automatically.
3.  **Standard Logging:** By using `logging.basicConfig(format=...)`, the logs go to `stdout`. In Kubernetes or Docker Swarm, standard tools automatically collect these logs and put them in systems like Datadog or CloudWatch. (This is why we removed the custom `remote_logger`).
4.  **Health Checks (`/health`):** Every service has a `/health` endpoint. In the cloud, a Load Balancer constantly pings `/health`. If a service stops responding, the Load Balancer kills it and starts a fresh copy automatically.

---

## 5. The Next Step: RabbitMQ (Asynchronous Messaging)

Currently, if the Word Service takes 5 seconds to process an image, the Gateway HTTP request waits for 5 seconds. If 100 users do this at once, the Gateway crashes (HTTP connection limits).

**The Solution:**
Instead of `Gateway -> HTTP -> Word Service`:
1.  **Gateway** drops a message (Image + Job ID) into a **RabbitMQ Queue** and immediately tells the user "Job Started."
2.  **Word Service** acts as a "Worker." It pulls messages from the Queue one by one. It never gets overwhelmed because the Queue holds the backlog.
3.  **Result:** When finished, the Word Service puts the answer in a "Result Queue" or saves it to a database (like Redis/PostgreSQL).

This pattern is essential for any heavy Machine Learning processing in production.
