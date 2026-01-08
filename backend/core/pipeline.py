from backend.core.model_registry import (
    helmet_model, plate_model, hsrp_model, ocr_model
)
from backend.core.rules import helmet_violation, hsrp_violation
from backend.services.cropper import crop_plates
from backend.services.storage import persist_pipeline_result

def run_pipeline(image, image_path=None):

    helmet_res = helmet_model.predict(image)
    plate_bboxes = plate_model.predict(image)

    result = {
        "helmet_detected": bool(helmet_res["helmet_detected"]),
        "helmet_confidence": float(helmet_res["confidence"]),
        "helmet_violation": bool(helmet_violation(
            helmet_res["helmet_detected"],
            helmet_res["confidence"]
        )),
        "plates": []
    }

    if not plate_bboxes:
        return {
            "event": result,
            "plates": []
        }

    crops = crop_plates(image, plate_bboxes)

    plates = []
    for idx, (bbox, crop) in enumerate(zip(plate_bboxes, crops)):
        hsrp_res = hsrp_model.predict(crop)
        ocr_res = ocr_model.predict(crop)
        print(ocr_res)

        plate = {
            "plate_id": int(idx),
            "bbox": [int(v) for v in bbox],
            "is_hsrp": bool(hsrp_res["is_hsrp"]),
            "hsrp_confidence": float(hsrp_res["confidence"]),
            "hsrp_violation": bool(
                hsrp_violation(
                    hsrp_res["is_hsrp"],
                    hsrp_res["confidence"]
                    )
            ),
            "ocr_text": str(ocr_res["text"]),
            "ocr_confidence": float(ocr_res["confidence"])
        }


        plates.append(plate)

    result["plates"] = plates

    if result["helmet_violation"] or any(p["hsrp_violation"] for p in plates):
        persist_pipeline_result(
            {
                "helmet_violation": result["helmet_violation"],
                "helmet_confidence": result["helmet_confidence"],
                "helmet_count": helmet_res.get("count", 1),
                "image_path": image_path
            },
            plates
        )

    return {
        "event": result,
        "plates": plates
    }
