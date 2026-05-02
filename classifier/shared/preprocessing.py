import io
from PIL import Image as PILImage, ImageOps
import torch
from torchvision import transforms
import numpy as np


# _CNN_TRANSFORM = transforms.Compose([
#     transforms.Grayscale(1),
#     transforms.Resize((28, 28)),
#     transforms.ToTensor(),
#     transforms.Normalize((0.1307,), (0.3081,)),
# ])



# we use the same transform for MobileNetV2, but with 3 channels (grayscale → RGB)
_MOBILENET_TRANSFORM = transforms.Compose([
    transforms.Grayscale(1),
    transforms.Resize((224, 224)),
    transforms.Grayscale(3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def _normalize_background(img: PILImage.Image) -> PILImage.Image:
    """
    Model trained on MNIST-style: dark background + bright ink.
    If input has bright background (mean > 127) → invert to match training.
    """
    gray = img.convert("L")
    if np.array(gray).mean() > 127:
        gray = ImageOps.invert(gray)
    return gray


# Main function to process the image
def preprocess_image(image_bytes: bytes, model_name: str) -> torch.Tensor:
    """Raw image bytes → (1, C, H, W) tensor, background-corrected."""
    tf  = _MOBILENET_TRANSFORM if model_name == "MobileNetV2" else _CNN_TRANSFORM
    img = _normalize_background(PILImage.open(io.BytesIO(image_bytes)))
    return tf(img).unsqueeze(0)






# ## doesn't work - word-service model doesn't work -----------------
# def preprocess_pil(pil_image: PILImage.Image, model_name: str) -> torch.Tensor:
#     """PIL Image → (1, C, H, W) tensor. Used by word service after segmentation."""
#     tf  = _MOBILENET_TRANSFORM if model_name == "MobileNetV2" else _CNN_TRANSFORM
#     return tf(_normalize_background(pil_image)).unsqueeze(0)