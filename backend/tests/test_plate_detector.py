import cv2
from pathlib import Path
from backend.core.model_registry import plate_model

BASE_DIR = Path(__file__).resolve().parents[2]
IMAGE_PATH = BASE_DIR / "test_images" / "test0.jpg"

# 🔽 Output directory for cropped plates
CROP_DIR = BASE_DIR / "test_outputs" / "plate_crops"
CROP_DIR.mkdir(parents=True, exist_ok=True)


def main():
    img = cv2.imread(str(IMAGE_PATH))
    if img is None:
        raise RuntimeError(f"Image not found: {IMAGE_PATH}")

    bboxes = plate_model.predict(img)

    print("\nPLATE DETECTOR OUTPUT")
    print("=" * 50)
    print(f"Plates detected: {len(bboxes)}")

    h, w = img.shape[:2]

    for idx, (x1, y1, x2, y2) in enumerate(bboxes):
        # 🔒 Clamp bbox to image boundaries
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            print(f"Skipping invalid bbox {idx}: {x1, y1, x2, y2}")
            continue

        # ✂️ Crop plate
        crop = img[y1:y2, x1:x2]

        # 💾 Save crop
        crop_path = CROP_DIR / f"plate_{idx}.jpg"
        cv2.imwrite(str(crop_path), crop)

        print(f"[{idx}] bbox={x1, y1, x2, y2} → saved: {crop_path}")

    print(f"\nImage shape: {img.shape}")


if __name__ == "__main__":
    main()
