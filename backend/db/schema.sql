-- ============================================================
-- Smart HSRP System Database Schema
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. EVENTS TABLE (Image-level inference)
-- ============================================================
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Helmet detection (image-level)
    helmet_violation BOOLEAN NOT NULL,
    helmet_confidence FLOAT,
    helmet_count INTEGER,

    -- Original uploaded image
    image_path TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_created_at
ON events(created_at);


-- ============================================================
-- 2. PLATE VIOLATIONS TABLE (Plate-level inference)
-- ============================================================
CREATE TABLE IF NOT EXISTS plate_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Parent image event
    event_id INTEGER NOT NULL,

    -- OCR & classification
    plate_text VARCHAR(20),
    is_hsrp BOOLEAN NOT NULL,
    hsrp_confidence FLOAT,
    ocr_confidence FLOAT,

    -- Cropped plate evidence
    plate_image_path TEXT,

    -- Bounding box (absolute pixel coords)
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_plate_event_id
ON plate_violations(event_id);

CREATE INDEX IF NOT EXISTS idx_plate_created_at
ON plate_violations(created_at);
