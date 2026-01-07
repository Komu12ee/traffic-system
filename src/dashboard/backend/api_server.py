"""
C3 - Backend API Server for Realtime Traffic Analytics
Receives events from inference engine
Serves latest event to dashboard frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from flask import Response
import cv2
import time
from collections import deque

latest_encoded_frame = None


app = Flask(__name__)
CORS(app)

# latest_event = {}   # Global shared state
# lock = threading.Lock()
event_queue = deque(maxlen=10)  # last 10 events store
lock = threading.Lock()


@app.route("/update", methods=["POST"])
def update():
    data = request.json

    with lock:
        event_queue.append(data)

    return {"status": "ok"}, 200


@app.route("/latest", methods=["GET"])
def latest():
    with lock:
        if len(event_queue) == 0:
            return jsonify({}), 200

        return jsonify(event_queue[-1]), 200


if __name__ == "__main__":
    print("[INFO] Starting Backend API on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
