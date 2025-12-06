"""
Inference Engine (B3)
Frame Grabber → YOLO Detector → Event Generator → JSON Output → FPS Logger
"""

import cv2
import time
import json
from ultralytics import YOLO
# from .model_loader import YOLOModelLoader
from src.inference.model_loader import YOLOModelLoader



class InferenceEngine:
    def __init__(self, stream_url, model_path="yolov8n.pt"):
        self.stream_url = stream_url
        self.model_loader = YOLOModelLoader(model_path=model_path, device="cpu")
        self.model = self.model_loader.get_model()

        print(f"[INFO] Opening camera stream: {stream_url}")
        self.cap = cv2.VideoCapture(stream_url)

        if not self.cap.isOpened():
            raise RuntimeError(f"[ERROR] Cannot open stream: {stream_url}")

        self.prev_time = time.time()

    def _compute_fps(self):
        current = time.time()
        fps = 1 / (current - self.prev_time)
        self.prev_time = current
        return round(fps, 2)

    def _detections_to_json(self, results):
        detections = []

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(float, box.xyxy[0])

            detections.append({
                "class_id": cls,
                "class_name": self.model.names[cls],
                "confidence": round(conf, 3),
                "bbox": [x1, y1, x2, y2]
            })

        return detections

    def run(self, display=True):
        print("[INFO] Starting inference loop... Press Q to exit.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] Frame read error")
                break

            results = self.model(frame, verbose=False)[0]

            detections_json = self._detections_to_json(results)
            fps = self._compute_fps()

            output = {
                "fps": fps,
                "num_detections": len(detections_json),
                "detections": detections_json
            }

            print(json.dumps(output, indent=2))

            if display:
                annotated = results.plot()
                cv2.imshow("Inference Engine - Press Q to exit", annotated)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        self.cap.release()
        cv2.destroyAllWindows()
