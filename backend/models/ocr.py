from paddleocr import PaddleOCR
import numpy as np

class PlateOCR:
    def __init__(self):
        # Minimal init for maximum compatibility
        self.ocr_engine = PaddleOCR(lang="en")

    def predict(self, plate_image: np.ndarray):
        """
        Safe OCR output:
        {
            "text": str,
            "confidence": float
        }
        """

        if plate_image is None or plate_image.size == 0:
            return {"text": "", "confidence": 0.0}

        try:
            plate_image = np.ascontiguousarray(plate_image, dtype=np.uint8)
            results = self.ocr_engine.ocr(plate_image)
        except Exception:
            # OCR failure should NEVER crash pipeline
            return {"text": "", "confidence": 0.0}

        if not results or not results[0]:
            return {"text": "", "confidence": 0.0}

        texts = []
        confidences = []

        for line in results[0]:
            # CASE 1: [box, (text, conf)]
            if (
                isinstance(line, (list, tuple))
                and len(line) == 2
                and isinstance(line[1], (list, tuple))
                and len(line[1]) == 2
            ):
                text = str(line[1][0])
                conf = float(line[1][1])

            # CASE 2: [box, text]
            elif (
                isinstance(line, (list, tuple))
                and len(line) == 2
                and isinstance(line[1], str)
            ):
                text = line[1]
                conf = 0.6  # default confidence

            # CASE 3: raw string
            elif isinstance(line, str):
                text = line
                conf = 0.5

            else:
                continue

            if text.strip():
                texts.append(text.strip())
                confidences.append(conf)

        if not texts:
            return {"text": "", "confidence": 0.0}

        return {
            "text": " ".join(texts),
            "confidence": sum(confidences) / len(confidences),
        }
