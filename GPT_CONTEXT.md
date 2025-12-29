# Project Context: Edge AI Smart Traffic Analytics

This file summarizes the repository so you can paste it into GPT to provide accurate context.

---

## 1) High-level summary

- Purpose: Edge AI vehicle detection + traffic metrics + alerts + live dashboard (proof-of-concept).
- Pipeline: Camera (phone IP webcam) → Inference (YOLOv8) → Metrics & Alerts → Backend API → Frontend Dashboard.
- Languages/Tech: Python (inference/backend), React + Vite + TypeScript (frontend), YOLO (ultralytics), OpenCV, Flask.

## 2) How to run (quick)

- Create Python env and install `requirements.txt` (uses `ultralytics`, `opencv-python`, `onnx`, `streamlit`, etc.).
- Start backend API: `python src/dashboard/backend/api_server.py` (runs on port 5001).
- Start inference: `python src/inference/run_inference.py` (edit `stream_url` or pass via args in future).
- Start frontend: `cd traffic-pulse-main && npm install && npm run dev` (Vite dev server).

## 3) Important files (summary)

- `src/inference/model_loader.py` — Loads YOLO model using `ultralytics.YOLO`, selects device (cuda/cpu).
- `src/inference/inference_engine.py` — Main inference loop: grabs frames, runs `model.track(...)`, converts detections → JSON, computes metrics, posts to backend `/update`, shows annotated frames, logs detections, sends email with `vehicle_log.csv` on stop.
- `src/inference/run_inference.py` — Entrypoint that instantiates `InferenceEngine` with a phone camera stream URL.
- `src/metrics/traffic_metrics.py` — Computes vehicle filtering, counts, class distribution, congestion score, and lane-wise counts.
- `src/alerts/alert_engine.py` — Alert logic for congestion, stationary/accident detection, wrong-way detection; exposes `generate_alerts(metrics,detections)`.
- `src/dashboard/backend/api_server.py` — Flask API that receives frames/metrics at `/update` and exposes current state at `/latest` for frontend.
- `src/stream/a5_test_stream.py` — Simple OpenCV-based stream tester.
- `src/utils/logger.py` — Writes `vehicle_log.csv` with detections.
- `src/utils/emailer.py` — Sends `vehicle_log.csv` via SMTP (Gmail) using provided credentials.
- `processing.ipynb` — Notebook with some processing/analysis cells.
- `requirements.txt` — Python dependencies list.
- `traffic-pulse-main/` — Frontend app (Vite + React + TypeScript) with many UI components and hooks.
  - `traffic-pulse-main/src/hooks/useTrafficData.ts` — Polls backend `/latest` and provides demo-mode when backend unavailable.

## 4) Data & model artifacts in repo

- `yolov8s.pt`, `yolov8n.onnx`, `yolov8n.pt` — model weights and exports (large binaries).
- `vehicle_log.csv` — runtime detection log file (created/used by logger/emailer).

## 5) Notable findings & issues (security, correctness, style)

- Hardcoded secrets: `src/inference/inference_engine.py` contains an SMTP `app_password` and email addresses. This is a sensitive secret and must be removed from source and stored in environment variables or a secrets manager.
- Committed binary & cache files: many `.pyc` files and heavy model weights (e.g., `yolov8s.pt`) are committed. Consider removing these from git history and adding to `.gitignore` (`*.pyc`, model weights, package-locks if not needed).
- Torch/CUDA usage issues:
  - `inference_engine.py` calls `torch.cuda.get_device_name(0)` unguarded — this raises if CUDA is unavailable.
  - `_detections_to_json` forcibly calls `.cuda()` on tensors without checking device, and `model.track(..., half=True)` may be incompatible with CPU-only runs.
  - `model_loader` warns not to call `.half()` but `inference_engine` still uses `half=True`.
- API robustness: `inference_engine` posts to `http://127.0.0.1:5001/update` with a very short timeout (0.05s) and swallows exceptions — OK for POC but hides errors.
- AlertEngine tracking: uses Python enumeration index as object identifier in tracking (`for idx, det in enumerate(detections)`), which is not a robust track ID across frames; better to use tracker-assigned IDs if available.
- Minor code issues:
  - Duplicate `@staticmethod` decorator in `traffic_metrics.py`.
  - Some try/except blocks swallow exceptions silently (e.g., printing device dtype exceptions) — consider logging.

## 6) Suggested immediate fixes (priority order)

1. Remove hardcoded credentials; replace with env vars and update `README.md` with required env vars (e.g., `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECEIVER`).
2. Add `.gitignore` entries and remove committed `.pyc` and large model files from git history (use `git rm --cached` then add to `.gitignore`; for history rewrite, use `git filter-repo` or `bfg`).
3. Guard CUDA calls: check `torch.cuda.is_available()` before calling `get_device_name(0)` or `.cuda()`; make `model.track` device-aware and avoid `half=True` on CPU.
4. Use tracker IDs (if using `ultralytics` tracker) rather than enumeration index for alert tracking.
5. Increase backend POST timeout, or handle failed connections more explicitly and log errors.

## 7) Recommended additions for GPT context (a prompt template)

When giving GPT the repository context, include these bullets (copy into your prompt):

- Project purpose: Edge AI traffic analytics using YOLO → metrics → alerts → dashboard.
- Run commands: `python src/dashboard/backend/api_server.py`, `python src/inference/run_inference.py`, `cd traffic-pulse-main && npm run dev`.
- Security note: `inference_engine.py` contains hardcoded SMTP credentials; treat them as secrets and do not expose.
- Key files: list from Section 3 above.
- Known issues: CUDA guards, `.pyc` and model files committed, use of `.cuda()` in code, duplicate decorators, naive alert tracking.

Example GPT prompt start:

"I have a Python/React project which implements an Edge AI traffic analytics pipeline. Key entry points: `src/inference/run_inference.py` (inference), `src/dashboard/backend/api_server.py` (backend), and `traffic-pulse-main/` (frontend). Please analyze design, point out security, performance, and correctness issues, and suggest a prioritized developer plan to make it production-ready. Note: repository currently has hardcoded SMTP credentials and committed model binaries."

## 8) Next steps I can do for you

- Generate a detailed per-file summary for every file (full walk) and store as `GPT_CONTEXT_FULL.md`.
- Create a `SECURITY.md` with actions to remove secrets and clean git history.
- Prepare PR suggestions to fix high-priority issues (guard CUDA calls, move secrets to env).

---

If you want, I can now produce the full per-file summaries (every file in `src/` and `traffic-pulse-main/src/`) and write them to `GPT_CONTEXT_FULL.md`. Reply "full summary" to proceed.
