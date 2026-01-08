import torch
import cv2
import numpy as np
from config.settings import settings


class HSRPClassifier:
    def __init__(self, model_path: str = settings.HSRP_MODEL_PATH):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = float(settings.HSRP_CONF_THRESHOLD)
        self.model = self._load_model(model_path)

        if self.model:
            print(f"HSRPClassifier: EfficientNet loaded on {self.device}")

    def _load_model(self, model_path):
        try:
            model = torch.jit.load(model_path, map_location=self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"Error loading HSRP model: {e}")
            return None

    def preprocess(self, img: np.ndarray):
        img = cv2.resize(img, (224, 224))
        img = img[:, :, ::-1]  # BGR → RGB
        img = img.astype(np.float32) / 255.0

        # ImageNet normalization (CRITICAL)
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img = (img - mean) / std

        img = np.transpose(img, (2, 0, 1))
        img = torch.tensor(img, dtype=torch.float32).unsqueeze(0)
        return img.to(self.device)

    def predict(self, plate_image: np.ndarray) -> dict:
        if plate_image is None:
            raise ValueError("Plate image is None")

        if self.model is None:
            return {
                "is_hsrp": None,
                "confidence": 0.0,
                "device_used": str(self.device)
            }

        input_tensor = self.preprocess(plate_image)

        with torch.no_grad():
            logit = self.model(input_tensor)
            non_hsrp_prob = torch.sigmoid(logit).item()  


        is_hsrp = non_hsrp_prob > self.threshold       # change less or greater than based on training or model

        return {
            "is_hsrp": is_hsrp,
            "confidence": float(round(1-non_hsrp_prob, 4)),
            "device_used": str(self.device)
        }
