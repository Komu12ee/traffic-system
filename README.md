
# 🚦 Traffic Pulse — Edge–Cloud AI Traffic Monitoring System

## 📌 Overview

**Traffic Pulse** is a real-time **Edge AI traffic analytics system** that performs high-speed vehicle detection and traffic analysis on an **edge GPU**, while asynchronously streaming **lightweight analytics** to a **cloud-hosted backend** for visualization.

The system is designed with a strong focus on **performance engineering, edge–cloud decoupling, and real-world deployment constraints**, rather than just model accuracy.

---

## 🎯 Key Objectives

- Perform **real-time vehicle detection and tracking** using YOLOv8
- Maintain **stable FPS on edge hardware**
- Avoid inference slowdown due to network latency
- Serve traffic analytics to a **cloud dashboard**
- Design a system that works reliably in **cloud environments (HF Spaces)**

---

## 🏗️ Final Architecture

```

Video / Camera
↓
Edge GPU (YOLOv8 Inference)
↓
Metrics & Alerts
↓
Async + Rate-Limited HTTP POST
↓
Cloud Backend (Hugging Face Space)
↓
/latest Endpoint
↓
React Dashboard

```

### Core Design Principle
> **Inference must never depend on network speed.**

---

## 🔁 End-to-End Data Flow

1. Frames are read from a video source using `VideoLoader`.
2. YOLOv8 performs detection and tracking on the edge GPU.
3. Traffic metrics are computed:
   - Vehicle count
   - Class distribution
   - Congestion score
   - Lane-wise counts
4. Alerts are generated based on rule-based logic.
5. Aggregated metrics are **sent asynchronously** to the cloud backend.
6. The backend exposes the latest analytics via `/latest`.
7. The React frontend polls `/latest` and updates the dashboard.

---

## ⚙️ Tech Stack

### Inference & Backend
- Python
- PyTorch
- YOLOv8 (Ultralytics)
- OpenCV
- Flask
- ThreadPoolExecutor (async I/O)
- Hugging Face Spaces

### Frontend
- React
- TypeScript
- Vite

---

## 📂 Project Structure

```

.
├── README.md
├── requirements.txt
├── yolov8s.pt
├── vehicle_log.csv
├── src/
│   ├── inference/
│   │   ├── inference_engine.py
│   │   ├── model_loader.py
│   ├── metrics/
│   │   └── traffic_metrics.py
│   ├── alerts/
│   │   └── alert_engine.py
│   ├── stream/
│   │   └── video_loader.py
│   ├── dashboard/
│   │   └── backend/
│   │       └── api_server.py
│   └── utils/
│       ├── logger.py
│       └── emailer.py
└── traffic-pulse-main/
    └── src/
        ├── hooks/useTrafficData.ts
        └── components/

```

---

## ⚡ Performance Optimizations

### Problem Encountered
FPS dropped when the backend was moved from local (`localhost`) to a cloud backend.

### Root Cause
- Blocking HTTP requests inside the inference loop
- Cloud network latency

### Solutions Implemented
- **Asynchronous backend communication**
- **Rate-limited backend updates** (every N frames)
- **Lightweight payloads** for cloud (metrics only)
- Inference kept fully local and non-blocking

### Result
- Stable FPS on edge GPU
- Responsive cloud dashboard
- Robust behavior under real network latency

---

## ▶️ Running the Project

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Run backend locally (optional)

```bash
python src/dashboard/backend/api_server.py
```

### 3️⃣ Set cloud backend URL

```bash
export BACKEND_URL=https://10komu-traffic-camera.hf.space/update
```

### 4️⃣ Run inference

```bash
python -m src.inference.run_inference
```

### 5️⃣ Run frontend

```bash
cd traffic-pulse-main
npm install
npm run dev
```

---

## How It Works
1. Capture: `VideoLoader` yields frames from a video file or camera.
2. Detect & track: `InferenceEngine` runs `YOLO.track()` and converts results to JSON.
3. Metrics: `TrafficMetrics` computes vehicle count, class distribution, congestion score (sum of bbox areas / frame area), and lane-wise counts.
4. Logging: `VehicleLogger` appends detections to `vehicle_log.csv` for later review.
5. Send: every N frames the engine schedules an async POST to `BACKEND_URL` (default points to the HF Space URL). The inference loop itself is not blocked by network I/O.
6. Backend: `api_server.py` stores incoming payloads in an in-memory deque and returns the latest via `/latest` for the dashboard.
7. Dashboard: the React frontend polls `/latest` and updates charts, cards and alerts.

---

## 🧠 Engineering Learnings

* Edge inference must be decoupled from network I/O
* Cloud backends introduce unavoidable latency
* Asynchronous communication is critical for real-time systems
* Cloud environments require fault-tolerant state handling
* Sending aggregated data is more scalable than streaming raw detections

---

## 🚀 Future Enhancements

* Replace polling with WebSockets or SSE
* Introduce Redis / message broker
* Persist metrics in a time-series database
* Add authentication and access control
* Containerize inference and backend

---

## 👤 Author

**Komendra Sahu**
M.Tech (Data Science & Artificial Intelligence)
Focus: Edge AI, Applied ML, MLOps


Key notes
- `inference_engine.py` rate-limits sends (`SEND_EVERY_N`) and uses a background worker (`ThreadPoolExecutor`) to avoid blocking inference.
- `api_server.py` keeps a small in-memory ring buffer (deque) of recent events and serves the latest via `/latest`.
- Frontend `useTrafficData.ts` polls the backend and falls back to demo data if the backend is unreachable.

---
