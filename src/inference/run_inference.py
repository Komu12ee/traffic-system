

from src.inference.inference_engine import InferenceEngine

if __name__ == "__main__":
    # IMPORTANT: Put your phone camera stream URL here
    stream_url = "http://10.243.180.130:8080/video"    # Example: "http://192.168.43.1:8080/video"

    engine = InferenceEngine(stream_url=stream_url, model_path="yolov8n.pt")
    engine.run(display=True)
