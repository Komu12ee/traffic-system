"""
Inference Engine (B3 + C1)
Frame Grabber → YOLO Detector → Metrics → JSON Output → FPS Logger
"""
import requests
import cv2
import time
import json
from ultralytics import YOLO

# IMPORT METRICS MODULE
from src.metrics.traffic_metrics import TrafficMetrics

# IMPORT MODEL LOADER
from src.inference.model_loader import YOLOModelLoader
from src.alerts.alert_engine import AlertEngine



class InferenceEngine:
    def __init__(self, stream_url, model_path="yolov8n.pt"):
        self.stream_url = stream_url
        self.model_loader = YOLOModelLoader(model_path=model_path, device="cpu")
        self.model = self.model_loader.get_model()
        self.alert_engine = AlertEngine()

        print(f"[INFO] Opening camera stream: {stream_url}")
        self.cap = cv2.VideoCapture(stream_url)

        if not self.cap.isOpened():
            raise RuntimeError(f"[ERROR] Cannot open stream: {stream_url}")

        self.prev_time = time.time()

    def _compute_fps(self):
        now = time.time()
        fps = 1 / (now - self.prev_time)
        self.prev_time = now
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

            # YOLO inference
            results = self.model(frame, verbose=False)[0]

            # Raw detections
            detections_json = self._detections_to_json(results)

            # Compute metrics from detections
            vehicle_detections = TrafficMetrics.filter_vehicles(detections_json)

            metrics = {
                "vehicle_count": TrafficMetrics.vehicle_count(vehicle_detections),
                "class_distribution": TrafficMetrics.class_distribution(vehicle_detections),
                "congestion_score": TrafficMetrics.congestion_score(
                    vehicle_detections, frame.shape[1], frame.shape[0]
                ),
                "lane_wise": TrafficMetrics.lane_wise_count(
                    vehicle_detections, frame.shape[1]
                )
            }

            fps = self._compute_fps()

            # Final Output JSON
            alerts = self.alert_engine.generate_alerts(metrics, vehicle_detections)

            output = {
                "fps": fps,
                "num_detections": len(detections_json),
                "detections": detections_json,
                "metrics": metrics,
                "alerts": alerts
            }
            try:
                 requests.post("http://127.0.0.1:5001/update", json=output, timeout=0.05)
            except:
                   pass  # ignore connection errors if backend not running



            print(json.dumps(output, indent=2))

            # Display annotated frame
            if display:
                annotated = results.plot()
                cv2.imshow("Inference Engine - Press Q to exit", annotated)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        self.cap.release()
        cv2.destroyAllWindows()
