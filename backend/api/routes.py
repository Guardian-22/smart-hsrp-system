from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
from backend.core.pipeline import run_pipeline
from backend.db.database import SessionLocal
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from backend.utils.converters import make_json_serializable

router = APIRouter()

@router.post("/detect")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    return run_pipeline(img)



# Add this to backend/api/routes.py

@router.get("/violations")
async def get_violations():
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT * FROM events ORDER BY created_at DESC LIMIT 100")
        )
        return [dict(row._mapping) for row in result]

