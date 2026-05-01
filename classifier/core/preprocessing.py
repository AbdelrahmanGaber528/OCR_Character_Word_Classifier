"""
shared/preprocess.py
Image → tensor pipeline.  Transforms match training exactly.
"""
import io
import torch
from PIL import Image as PILImage
from torchvision import transforms

_CNN_TF = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((28, 28)),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,)),
])

_MOBILENET_TF = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def _get_tf(model_name: str) -> transforms.Compose:
    return _MOBILENET_TF if model_name == "MobileNetV2" else _CNN_TF


def bytes_to_tensor(image_bytes: bytes, model_name: str) -> torch.Tensor:
    """Raw image bytes  →  (1, C, H, W) tensor."""
    img = PILImage.open(io.BytesIO(image_bytes)).convert("L")
    return _get_tf(model_name)(img).unsqueeze(0)


def pil_to_tensor(pil_img: PILImage.Image, model_name: str) -> torch.Tensor:
    """PIL Image  →  (1, C, H, W) tensor.  Used by word segmentation."""
    return _get_tf(model_name)(pil_img.convert("L")).unsqueeze(0)