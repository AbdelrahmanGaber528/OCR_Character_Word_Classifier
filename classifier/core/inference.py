import torch
import os
from .models import load_model
from .preprocessing import preprocess_image

MODEL = None
CLASS_NAMES = None
MODEL_NAME = None

def get_prediction(image_bytes: bytes):

    global MODEL, CLASS_NAMES, MODEL_NAME
    
    if MODEL is None:
        path = os.getenv("MODEL_PATH", "model/ocr_model.pth")
        MODEL, CLASS_NAMES, MODEL_NAME = load_model(path)
    
    input_tensor = preprocess_image(image_bytes, MODEL_NAME)
    
    with torch.no_grad():
        outputs = MODEL(input_tensor)
        prob = torch.nn.functional.softmax(outputs[0], dim=0)
        conf, idx = torch.max(prob, dim=0)
    
    return CLASS_NAMES[idx.item()], conf.item()