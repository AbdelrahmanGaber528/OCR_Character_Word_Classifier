from fastapi import FastAPI, File, UploadFile
from core.inference import get_prediction 
from core.segmentation import segment_characters
import io

app = FastAPI(title="OCR Classifier Service")

@app.get("/health")
async def health():
    return {"status": "ready", "model": "loaded"}

@app.post("/predict-character")
async def predict_char(file: UploadFile = File(...)):
    image_bytes = await file.read()
    char, confidence = get_prediction(image_bytes)
    return {"prediction": char, "confidence": round(confidence, 4)}

@app.post("/predict-word")
async def predict_word(file: UploadFile = File(...)):
    image_bytes = await file.read()
    crops = segment_characters(image_bytes)
    
    full_word = ""
    for crop in crops:
        char, _ = get_prediction(crop)
        full_word += char
        
    return {"prediction": full_word}