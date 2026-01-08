import torch
import numpy as np
from ultralytics import YOLO
from config.settings import settings

class HelmetDetector:
    def __init__(self, model_path: str=settings.HELMET_MODEL_PATH):
        """
        Initializes the YOLO model for helmet detection.
        """
        self.model_path = model_path
        # Detect device: if  GPU, CPU otherwise
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self._load_model()

        if self.model:
            print(f"HelmetDetector: Model loaded on {self.device}")

    def _load_model(self):
        """
        Loads the YOLO model weights.
        """
        try:
            # Loads pre-trained or custom helmet weights
            return YOLO(self.model_path)
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def predict(self, image: np.ndarray) -> dict:
        """
        Predicts helmet presence using YOLO inference.
        """
        if image is None:
            raise ValueError("Invalid image passed to HelmetDetector")

        if self.model is None:
            raise RuntimeError("Helmet detection model not loaded")

        # Perform inference
        # results[0].boxes contains detections
        results = self.model(image, conf=0.5, verbose=False)
        
        # Logic: Check if any detected object belongs to 'helmet' class
        # (class 0 is 'helmet' in the model)
        detections = results[0].boxes
        helmet_detected = len(detections) > 0
        
        # Get highest confidence score if detections exist
        # Use .cpu() to safely transfer the value for Python float conversion
        confidence = float(detections.conf.max().cpu()) if helmet_detected else 0.0


        return {
            "helmet_detected": helmet_detected,
            "confidence": round(confidence, 4),
            "count": len(detections),
            "device_used": str(self.device)
        }
