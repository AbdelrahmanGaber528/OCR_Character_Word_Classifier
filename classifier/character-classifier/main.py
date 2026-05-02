import os
import logging
from contextlib import asynccontextmanager

import torch
import torch.nn.functional as F
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

from shared.model_loader import load_model
from shared.preprocessing import preprocess_image
from shared.remote_logger import RemoteLogger

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model/ocr_model.pth")
DEVICE     = os.getenv("DEVICE", "cpu")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | character | %(message)s")
remote_log = RemoteLogger("character-service")



# on startup

ml: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI): # this function is used instead of startup() and shutdown events to load the model once when the app starts . version in fastapi
    await remote_log.info(f"Loading model from {MODEL_PATH} ...")
    model, class_names, model_name = load_model(MODEL_PATH, device=DEVICE)
    ml.update(model=model, class_names=class_names, model_name=model_name)
    await remote_log.info(f"Ready — {model_name} | {len(class_names)} classes | {DEVICE}")
    yield
    ml.clear()



app = FastAPI(title="Character Service",
            description='character-prediction for letters',
            lifespan=lifespan)



# schema of predicted letter
class Prediction(BaseModel):
    label: str
    confidence: float

class CharResponse(BaseModel):
    predicted_letter: str
    confidence: float
    model_used: str
    top_k: list[Prediction]




@torch.no_grad()
def _run(image_bytes: bytes, k: int = 3) -> CharResponse:
    tensor = preprocess_image(image_bytes, ml["model_name"]).to(DEVICE)

    logits = ml["model"](tensor)
    probs  = F.softmax(logits, dim=1).squeeze()

    top_probs, top_indices = torch.topk(probs, k=min(k, len(ml["class_names"])))

    predictions = [
        Prediction(
            label=ml["class_names"][idx.item()],
            confidence=round(prob.item(), 4)
        )
        for prob, idx in zip(top_probs, top_indices)
    ]

    return CharResponse(
        predicted_letter=predictions[0].label,
        confidence=predictions[0].confidence,
        model_used=ml["model_name"],
        top_k=predictions,
    )





@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": ml.get("model_name"),
        "device": DEVICE
    }





@app.post("/predict-character", response_model=CharResponse)
async def predict_character(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be an image file.")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")

    try:
        res = _run(data, k=3)
        await remote_log.info(f"Predicted character: {res.predicted_letter} (conf: {res.confidence})")
        return res
    except Exception as e:
        await remote_log.error(f"Inference error: {e}")
        raise HTTPException(500, str(e))