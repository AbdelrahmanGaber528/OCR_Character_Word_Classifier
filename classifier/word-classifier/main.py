import os
import io
import logging
from contextlib import asynccontextmanager

import numpy as np
import easyocr
from PIL import Image as PILImage
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel





DEVICE     = os.getenv("DEVICE", "cpu")
USE_GPU    = DEVICE == "cpu"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger     = logging.getLogger("word-service")




ml: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading EasyOCR reader ...")
    reader = easyocr.Reader(["en"], gpu=USE_GPU, verbose=False)
    ml.update(reader=reader)
    logger.info(f"EasyOCR ready | gpu={USE_GPU}")
    yield
    ml.clear()


app = FastAPI(title="Word Service", lifespan=lifespan)




class CharResult(BaseModel):
    position: int
    letter: str
    confidence: float

class WordResponse(BaseModel):
    predicted_word: str
    characters: list[CharResult]
    num_chars_detected: int
    avg_confidence: float
    model_used: str
    warning: str | None = None



def _run(image_bytes: bytes) -> WordResponse:
    # Convert bytes → numpy RGB array (EasyOCR expects RGB)
    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)

    # EasyOCR returns: [([[box_coords]], text, confidence), ...]
    results = ml["reader"].readtext(arr, detail=1, paragraph=False)

    if not results:
        return WordResponse(
            predicted_word="",
            characters=[],
            num_chars_detected=0,
            avg_confidence=0.0,
            model_used="EasyOCR",
            warning="No text detected in image.",
        )

    # Join all detected segments, uppercase to match character service
    full_text = " ".join(r[1] for r in results).upper()
    avg_conf  = round(sum(r[2] for r in results) / len(results), 4)

    # Per-character breakdown (skip spaces)
    characters = [
        CharResult(position=i, letter=ch, confidence=avg_conf)
        for i, ch in enumerate(full_text)
        if ch != " "
    ]

    warning = None
    if avg_conf < 0.5:
        warning = "Low confidence. Try a clearer image with better contrast."

    return WordResponse(
        predicted_word=full_text,
        characters=characters,
        num_chars_detected=len(characters),
        avg_confidence=avg_conf,
        model_used="EasyOCR",
        warning=warning,
    )





# endpoints
@app.get("/health")
def health():
    return {"status": "ok", "model": "EasyOCR", "device": DEVICE}


@app.post("/predict-word", response_model=WordResponse)
async def predict_word(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be an image file.")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")

    try:
        res = _run(data)
        logger.info(
            f"Predicted: '{res.predicted_word}' | "
            f"conf={res.avg_confidence} | chars={res.num_chars_detected}"
        )
        return res
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(500, str(e))
