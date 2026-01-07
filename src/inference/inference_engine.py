"""
Inference Engine
Video Loader → YOLO Detector → Metrics → Alerts → Backend → Dashboard
"""

import os
import time
import json
import requests
import cv2
import torch

from src.utils.logger import VehicleLogger
from src.utils.emailer import EmailSender
from src.metrics.traffic_metrics import TrafficMetrics
from src.inference.model_loader import YOLOModelLoader
from src.alerts.alert_engine import AlertEngine
try:
    # Prefer the project's VideoLoader if available
    from src.stream.video_loader import VideoLoader  # type: ignore
except Exception:
    # Fallback lightweight VideoLoader in case import fails (keeps runtime resilient)
    import cv2

    class VideoLoader:
        def __init__(self, video_path):
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise ValueError(f"Cannot open video source: {video_path}")

        def frames(self):
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                yield frame

        def release(self):
            self.cap.release()


# -----------------------------
# Device & CUDA safety
# -----------------------------
CUDA_AVAILABLE = torch.cuda.is_available()
print("CUDA Available:", CUDA_AVAILABLE)

if CUDA_AVAILABLE:
    print("Current Device:", torch.cuda.get_device_name(0))
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True


class InferenceEngine:
    def __init__(self, video_path: str, model_path: str = "yolov8n.pt"):
        """
        video_path : path to input video file
        model_path : YOLO model weights
        """
        from concurrent.futures import ThreadPoolExecutor

        self.backend_executor = ThreadPoolExecutor(max_workers=1)
        self.frame_id = 0
        self.SEND_EVERY_N = 8   # ya 10 (HF ke liye)

        # -----------------------------
        # Video input (decoupled)
        # -----------------------------
        self.video_loader = VideoLoader(video_path)
        print(f"[INFO] Video source loaded: {video_path}")

        # -----------------------------
        # Model
        # -----------------------------
        self.model_loader = YOLOModelLoader(
            model_path=model_path,
            device="auto"
        )
        self.model = self.model_loader.get_model()

        # -----------------------------
        # Pipeline components
        # -----------------------------
        self.alert_engine = AlertEngine()
        self.logger = VehicleLogger()

        # -----------------------------
        # Email (secrets via env vars)
        # -----------------------------
        self.emailer = EmailSender(
            sender_email="chetanjaysingh500@gmail.com",
            app_password="yndq wzax uxou rnyq",
            receiver_email="sahukomendra721@gmail.com",
        )

        self.prev_time = time.time()

    # send to backend 
    def _send_to_backend(self, url, payload, timeout):
     """
      Non-blocking backend sender (runs in background thread)
     """
     try:
         requests.post(url, json=payload, timeout=timeout)
     except Exception as e:
         print(f"[WARN] Backend send failed: {e}")

    # -----------------------------
    # FPS calculation
    # -----------------------------
    def _compute_fps(self):
        now = time.time()
        fps = 1 / max(now - self.prev_time, 1e-6)
        self.prev_time = now
        return round(fps, 2)

    # -----------------------------
    # Convert YOLO detections to JSON
    # -----------------------------
    def _detections_to_json(self, results, conf_thresh=0.6):
        detections = []

        boxes = results.boxes.xyxy
        confs = results.boxes.conf
        clss = results.boxes.cls
        ids = results.boxes.id if results.boxes.id is not None else None

        for i in range(len(boxes)):
            conf = float(confs[i].item())
            if conf < conf_thresh:
                continue

            cls = int(clss[i].item())
            x1, y1, x2, y2 = map(float, boxes[i].tolist())

            track_id = int(ids[i].item()) if ids is not None else -1

            detections.append({
                "track_id": track_id,
                "class_id": cls,
                "class_name": self.model.names[cls],
                "confidence": round(conf, 3),
                "bbox": [x1, y1, x2, y2],
            })

        return detections

    # -----------------------------
    # Main loop
        # -----------------------------
    def run(self, display: bool = True):
        print("[INFO] Starting inference loop... Press Q to exit.")
    
        backend_url = os.getenv(
            "BACKEND_URL",
            "https://10komu-traffic-camera.hf.space/update"
        )
        timeout = float(os.getenv("BACKEND_TIMEOUT", "2.0"))
    
        for frame in self.video_loader.frames():
    
            self.frame_id += 1
    
            # --------------------------------------------------
            # 1️⃣ YOLO inference (UNCHANGED)
            # --------------------------------------------------
            results = self.model.track(
                frame,
                imgsz=640,
                half=CUDA_AVAILABLE,
                persist=True
            )[0]
    
            # --------------------------------------------------
            # 2️⃣ Detections + logging (local)
            # --------------------------------------------------
            detections_json = self._detections_to_json(results)
            self.logger.log(detections_json)
    
            # --------------------------------------------------
            # 3️⃣ Metrics
            # --------------------------------------------------
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
            alerts = self.alert_engine.generate_alerts(metrics, vehicle_detections)
    
            # --------------------------------------------------
            # 4️⃣ OUTPUT PAYLOADS
            # --------------------------------------------------
    
            # FULL payload (local use only)
            output = {
                "fps": fps,
                "num_detections": len(detections_json),
                "detections": detections_json,
                "metrics": metrics,
                "alerts": alerts
            }
    
            # LIGHT payload (HF backend)
            light_output = {
                "fps": fps,
                "metrics": metrics,
                "alerts": alerts
            }
    
            # --------------------------------------------------
            # 5️⃣ ASYNC BACKEND SEND (RATE LIMITED)
            # --------------------------------------------------
            if self.frame_id % self.SEND_EVERY_N == 0:
                self.backend_executor.submit(
                    self._send_to_backend,
                    backend_url,
                    output,
                    timeout
                )
    
            # --------------------------------------------------
            # 6️⃣ OPTIONAL DISPLAY (FPS killer if always on)
            # --------------------------------------------------
            if display:
                annotated = results.plot()
                cv2.imshow("Inference Engine - Press Q to exit", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    
        # ------------------------------------------------------
        # CLEANUP
        # ------------------------------------------------------
        self.video_loader.release()
        cv2.destroyAllWindows()
    
        self.emailer.send_log("vehicle_log.csv")
        print("[INFO] CSV email sent. Inference session completed.")
    
    
    
    
    
    
    
    
    
    
    