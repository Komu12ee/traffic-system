**Issue Summary**
- **Problem:** Inference engine posts JSON to https://10komu-traffic-camera.hf.space/update, but dashboard `/latest` shows no data (or returns 500).  
- **Expected:** Each inference POST updates the server’s latest state so GET `/latest` returns the most recent JSON.

**Environment**
- **Repo files:** `src/inference/inference_engine.py`, `src/dashboard/backend/api_server.py`, `traffic-pulse-main/src/hooks/useTrafficData.ts`
- **Backend host:** https://10komu-traffic-camera.hf.space (Hugging Face Space)
- **Local dev:** backend normally runs on `http://127.0.0.1:5001` (server uses `host="0.0.0.0", port=5001`)
- **Client:** inference engine (Python) posts JSON every frame; frontend polls `/latest`.

**Observed responses**
- `GET https://10komu-traffic-camera.hf.space/latest` → HTTP 500 (Internal Server Error)
- `POST https://10komu-traffic-camera.hf.space/update` → HTTP 200 with body `{"status":"ok"}` (tested with curl from the inference machine)

**Steps to reproduce**
1. Start the backend locally (if testing local):  
   `python src/dashboard/backend/api_server.py`
2. From the inference machine (or same host), test POST:  
   `curl -v https://10komu-traffic-camera.hf.space/update -X POST -H "Content-Type: application/json" -d '{"test":1}'`
3. Then GET latest:  
   `curl -v https://10komu-traffic-camera.hf.space/latest`
4. Run inference ensuring env is set:  
   `export BACKEND_URL=https://10komu-traffic-camera.hf.space/update`  
   `export BACKEND_TIMEOUT=5.0`  
   `python -m src.inference.inference_engine <video_path>`

**Logs / Evidence (from my tests)**
- POST to `/update` returned `200 {"status":"ok"}`.
- GET `/latest` returned `500 Internal Server Error` and HTML error page.
- Inference prints either success/warn/error messages when posts fail — I patched the engine to read `BACKEND_URL`/`BACKEND_TIMEOUT` at runtime.

**What I’ve tried**
- Verified remote `/update` accepts POSTs (HTTP 200).
- Observed remote `/latest` returns 500 — indicates server-side error when serializing/returning latest state.
- Patched `src/inference/inference_engine.py` so `BACKEND_URL` and `BACKEND_TIMEOUT` are read at runtime and used by async sender.
- Patched frontend hook to prefer a localhost backend only when served from `localhost` (but defaults still point to HF Space).

**Likely causes**
- The Hugging Face Space app has an internal error when handling GET `/latest` (server-side exception). This explains 500 even though POST returned 200.
- Alternatively, HF Space may accept POST (enqueue) but fail when returning `latest_event` (e.g., serialization of unexpected data, concurrency issue).
- If inference is running in different environment without the correct `BACKEND_URL`, data might be sent elsewhere — confirm inference logs show the `backend_url` used.

**Requested actions / questions for support (copy this to HF support or a teammate)**
- Please check the HF Space app logs for errors/exceptions happening on GET `/latest`. Look for stack traces around the time I did a `curl /latest` that returned 500.
- Confirm `/update` actually writes to the in-memory `latest_event` and that `latest()` returns `jsonify(latest_event)` without raising (see `src/dashboard/backend/api_server.py`).
- If you see an exception, please paste the stack trace and indicate which object failed to serialize or which global state was None/invalid.
- If the Space uses persistent storage or process restarts, confirm whether `/update` and `/latest` are handled by the same process/replica (race/replica routing can cause missing data).
- Advise if any request size, content, or security filter on the Space might accept a simple test POST but reject or error when returning a full inference payload (large nested arrays).

**What I can provide**
- Full curl request/response logs (I can attach verbose outputs).  
- Example JSON payload from the inference engine (large but available).  
- Exact git diff of changes I made in `src/inference/inference_engine.py` and `traffic-pulse-main/src/hooks/useTrafficData.ts`.

**Immediate next debugging steps I can perform**
- Add a debug log in `api_server.py` entering `/update` and before returning in `/latest` to reproduce the exception locally.  
- Re-run `curl -v /latest` and capture server logs.  
- Temporarily reduce inference payload size and retest to see if serialization/size triggers error.

Please let me know which log files I should fetch from the HF Space (or if you want me to run a targeted test and paste the verbose outputs).
