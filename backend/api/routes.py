from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
from backend.core.pipeline import run_pipeline
from backend.db.database import SessionLocal
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from backend.utils.converters import make_json_serializable
from backend.core.pipeline import persist_pipeline_result

router = APIRouter()

@router.post("/detect")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    return run_pipeline(img , force_save=False)



# Add this to backend/api/routes.py

@router.get("/violations")
async def get_violations():
    with SessionLocal() as session:

        # 1️⃣ Fetch events
        events = session.execute(
            text("""
                SELECT
                    id,
                    helmet_violation,
                    helmet_confidence,
                    helmet_count,
                    image_path,
                    created_at
                FROM events
                ORDER BY created_at DESC
                LIMIT 100
            """)
        ).fetchall()

        response = []

        # 2️⃣ Fetch plates per event
        for event in events:
            event_id = event.id

            plates = session.execute(
                text("""
                    SELECT
                        plate_text,
                        is_hsrp,
                        hsrp_confidence,
                        ocr_confidence
                    FROM plate_violations
                    WHERE event_id = :event_id
                """),
                {"event_id": event_id}
            ).fetchall()

            plate_list = []
            for p in plates:
                plate_list.append({
                    "ocr_text": p.plate_text,
                    "is_hsrp": bool(p.is_hsrp),
                    "hsrp_confidence": p.hsrp_confidence,
                    "ocr_confidence": p.ocr_confidence
                })

            response.append({
                "id": event.id,
                "helmet_violation": bool(event.helmet_violation),
                "helmet_confidence": event.helmet_confidence,
                "helmet_count": event.helmet_count,
                "image_path": event.image_path,
                "created_at": event.created_at,
                "plates": plate_list
            })

        return response


    

@router.post("/save")
async def save_record(payload: dict):
    event = payload.get("event")
    plates = payload.get("plates")
    force_save = payload.get("force_save", False)

    if not event or plates is None:
        raise HTTPException(status_code=400, detail="Invalid payload")

    persist_pipeline_result(event, plates)

    return {"status": "saved"}



