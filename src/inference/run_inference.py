from src.inference.inference_engine import InferenceEngine

if __name__ == "__main__":
    stream = "http://10.224.240.144:8080/video"  # your phone IP
    engine = InferenceEngine(stream_url=stream, model_path="yolov8n.pt")
    engine.run(display=True)
