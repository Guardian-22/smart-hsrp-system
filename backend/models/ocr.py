from paddleocr import PaddleOCR
import numpy as np
import cv2

class PlateOCR:
    def __init__(self):
        self.ocr_engine = PaddleOCR(
            lang="en",
            use_angle_cls=True
        )

    def predict(self, plate_image: np.ndarray):
        """
        Returns:
        {
            "text": str,
            "confidence": float
        }
        """

        if plate_image is None or plate_image.size == 0:
            return {"text": "", "confidence": 0.0}

        # --- Preprocessing (same as isolated test) ---
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        plate_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        try:
            results = self.ocr_engine.predict(plate_image)
        except Exception as e:
            print("OCR ERROR:", e)
            return {"text": "", "confidence": 0.0}

        if not results or results[0] is None:
            return {"text": "", "confidence": 0.0}

        result = results[0]

        texts = result.get("rec_texts", [])
        scores = result.get("rec_scores", [])

        if not texts or not scores:
            return {"text": "", "confidence": 0.0}

        # Clean & merge text
        final_text = "".join(t.replace(" ", "").upper() for t in texts)
        avg_conf = sum(scores) / len(scores)

        return {
            "text": final_text,
            "confidence": round(float(avg_conf), 4)
        }
