import torch
import torch.nn as nn
from torchvision import models as tv_models



# class OCR_CNN(nn.Module):
#     """Custom CNN for 28×28 grayscale input."""
#     def __init__(self, num_classes: int = 26):
#         super().__init__()
#         self.block1 = nn.Sequential(
#             nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
#             nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
#             nn.MaxPool2d(2, 2), nn.Dropout2d(0.25),
#         )
#         self.block2 = nn.Sequential(
#             nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
#             nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
#             nn.MaxPool2d(2, 2), nn.Dropout2d(0.25),
#         )
#         self.block3 = nn.Sequential(
#             nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
#             nn.AdaptiveAvgPool2d(1),
#         )
#         self.head = nn.Sequential(
#             nn.Flatten(),
#             nn.Linear(128, 256), nn.ReLU(inplace=True),
#             nn.Dropout(0.5),
#             nn.Linear(256, num_classes),
#         )

#     def forward(self, x: torch.Tensor) -> torch.Tensor:
#         return self.head(self.block3(self.block2(self.block1(x))))



def _build_mobilenetv2(num_classes: int) -> nn.Module:
    model = tv_models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes),
    )
    return model



def load_model(checkpoint_path: str, device: str = "cpu"):
    """
    Load OCR model from checkpoint.

    Returns
    -------
    model       : nn.Module  (eval mode)
    class_names : list[str]
    model_name  : str  ('OCR_CNN' | 'MobileNetV2')
    """
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)

    model_name  = ckpt["model_name"]
    num_classes = ckpt["num_classes"]
    class_names = ckpt["class_names"]

    model = _build_mobilenetv2(num_classes) if model_name == "MobileNetV2" else OCR_CNN(num_classes)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    return model, class_names, model_name