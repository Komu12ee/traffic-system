"""
model_loader.py
Handles loading YOLOv8 model in a modular, configurable way.
Supports: CPU-only, ONNX switching (future), quantized models.
"""

from ultralytics import YOLO
import torch
import os


class YOLOModelLoader:
    def __init__(self, model_path="yolov8n.pt", device=None):
        """
        model_path : path to YOLO weights or ONNX file
        device : "cpu" or "cuda". If None → auto-select.
        """

        # Auto-device selection
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.model_path = model_path

        print(f"[INFO] Loading YOLO model: {model_path}")
        print(f"[INFO] Device selected: {self.device}")

        # Load YOLOv8 model
        self.model = YOLO(model_path)
        self.model.to(self.device)

        print("[INFO] YOLO model loaded successfully.")

    def predict(self, frame):
        """
        Runs inference on a single frame.
        Returns YOLO results object.
        """
        results = self.model(frame, verbose=False)
        return results

    def get_model(self):
        return self.model


if __name__ == "__main__":
    # Quick test
    loader = YOLOModelLoader(model_path="yolov8n.pt")
    print("Model names:", loader.model.names)
