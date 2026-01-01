

from src.inference.inference_engine import InferenceEngine

if __name__ == "__main__":
    # IMPORTANT: Put your phone camera stream URL here
    # stream_url = "http://10.243.180.15:8080/video"    # Example: "http://192.168.43.1:8080/video"
    stream_url = "data/sample_vedio/traffic_video.mp4"
    # engine = InferenceEngine(stream_url=stream_url, model_path="yolov8n.pt")
    engine = InferenceEngine(video_path=stream_url, model_path="yolov8s.pt")

    engine.run(display=True)
