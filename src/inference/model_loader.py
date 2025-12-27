"""
model_loader.py
Handles loading YOLOv8 model in a modular, configurable way.
Supports: CPU-only, ONNX switching (future), quantized models.
"""

from ultralytics import YOLO
import torch
import os


class YOLOModelLoader:
    def __init__(self, model_path="yolov8n.pt", device="auto"):
        # Device select
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[INFO] Selected device: {self.device}")

        # Load YOLO model
        self.model = YOLO(model_path)

        # Move to device (GPU/CPU)
        self.model.to(self.device)

        # ❌ IMPORTANT: yahan .half() MAT LAGANA abhi
        # self.model.model.half()  # <-- remove this if you had it

        # Debug info
        try:
            p = next(self.model.model.parameters())
            print("[INFO] Model param device:", p.device)
            print("[INFO] Model param dtype :", p.dtype)
        except Exception:
            pass

    def get_model(self):
        return self.model


if __name__ == "__main__":
    # Quick test
    loader = YOLOModelLoader(model_path="yolov8n.pt")
    print("Model names:", loader.model.names)
