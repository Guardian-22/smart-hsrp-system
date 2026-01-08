import cv2
from pathlib import Path
from backend.core.model_registry import helmet_model

BASE_DIR = Path(__file__).resolve().parents[2]
IMAGE_PATH = BASE_DIR / "test_images" / "test2.jpg"

def main():
    img = cv2.imread(str(IMAGE_PATH))
    if img is None:
        raise RuntimeError(f"Image not found: {IMAGE_PATH}")

    res = helmet_model.predict(img)

    print("\nHELMET DETECTOR OUTPUT")
    print("=" * 50)
    for k, v in res.items():
        print(f"{k:20}: {v}")

if __name__ == "__main__":
    main()
