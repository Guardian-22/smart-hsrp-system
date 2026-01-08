from backend.db.database import SessionLocal
from sqlalchemy import text

def persist_pipeline_result(event_data, plates):
    session = SessionLocal()

    session.execute(
        text("""
        INSERT INTO events (helmet_violation, helmet_confidence, helmet_count, image_path)
        VALUES (:hv, :hc, :hcount, :ip)
        """),
        {
            "hv": event_data["helmet_violation"],
            "hc": event_data["helmet_confidence"],
            "hcount": event_data["helmet_count"],
            "ip": event_data["image_path"]
        }
    )

    event_id = session.execute(
        text("SELECT last_insert_rowid()")
    ).scalar()

    for p in plates:
        session.execute(
            text("""
            INSERT INTO plate_violations
            (event_id, plate_text, is_hsrp, hsrp_confidence, ocr_confidence,
             bbox_x1, bbox_y1, bbox_x2, bbox_y2)
            VALUES (:eid, :pt, :ih, :hc, :oc, :x1, :y1, :x2, :y2)
            """),
            {
                "eid": event_id,
                "pt": p["ocr_text"],
                "ih": p["is_hsrp"],
                "hc": p["hsrp_confidence"],
                "oc": p["ocr_confidence"],
                "x1": p["bbox"][0],
                "y1": p["bbox"][1],
                "x2": p["bbox"][2],
                "y2": p["bbox"][3],
            }
        )

    session.commit()
    session.close()
