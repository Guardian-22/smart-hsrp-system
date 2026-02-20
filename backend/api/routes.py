"""
API ROUTES - FIXED
===========
All backend API endpoints for Smart HSRP Monitoring System.

FIXES:
- Better error logging with full traceback
- Proper exception propagation
- Enhanced job status reporting
- Added logging configuration
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import FileResponse
import numpy as np
import cv2
import tempfile
import os
import threading
from uuid import uuid4
from typing import Optional, List
from pathlib import Path
import logging
import traceback
import sys

from backend.core.video_pipeline import process_video, generate_violation_summary
from backend.services.storage import (
    store_violations_batch,
    get_violations,
    save_threshold_state,
    load_threshold_state,
)
from backend.db.database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job store
JOB_STORE: dict = {}


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────
# VIDEO PROCESSING (ASYNC)
# ─────────────────────────────────────────────

@router.post("/process-video")
async def process_video_endpoint(
    file:                   UploadFile = File(...),
    frame_skip:             int  = Form(1),
    save_output_video:      bool = Form(True),
    annotate_violations:    bool = Form(True),
    annotate_no_violations: bool = Form(False),
    ocr_mode:               str  = Form("always"),
):
    """Upload a video and start async processing."""
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        video_path = tmp.name

    job_id = str(uuid4())
    output_video_path = None
    if save_output_video:
        out_dir = Path("static/outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        output_video_path = str(out_dir / f"{job_id}_annotated.mp4")

    JOB_STORE[job_id] = {
        "status": "running",
        "filename": file.filename,
        "progress": 0,
        "total_frames": 0,
    }
    
    logger.info(f"Job {job_id} started for file: {file.filename}")
    logger.info(f"  Video path: {video_path}")
    logger.info(f"  Output path: {output_video_path}")
    logger.info(f"  Frame skip: {frame_skip}")
    logger.info(f"  Annotate violations: {annotate_violations}")
    logger.info(f"  Annotate no violations: {annotate_no_violations}")
    logger.info(f"  OCR mode: {ocr_mode}")

    def background_task():
        try:
            logger.info(f"Job {job_id}: Starting video processing...")
            
            def progress_cb(frames_processed, total):
                JOB_STORE[job_id]["progress"] = frames_processed
                JOB_STORE[job_id]["total_frames"] = total if isinstance(total, int) else 0
                if frames_processed % 50 == 0:
                    logger.info(f"Job {job_id}: Processed {frames_processed} frames")
            
            output = process_video(
                video_path=video_path,
                output_video_path=output_video_path,
                frame_skip=frame_skip,
                enable_tracking=True,
                enable_ocr_stabilization=True,
                enable_temporal_fusion=True,
                enable_prediction=True,
                enable_adaptive_thresholds=True,
                enable_db_gating=True,
                annotate_violations=annotate_violations,
                annotate_no_violations=annotate_no_violations,
                ocr_mode=ocr_mode,
                progress_callback=progress_cb,
            )

            logger.info(f"Job {job_id}: Processing complete")
            logger.info(f"  Frames processed: {output['metadata'].get('total_frames_processed', 0)}")
            logger.info(f"  Violations found: {len(output.get('violations', []))}")
            logger.info(f"  Tracks: {len(output.get('track_summaries', {}))}")

            # Store violations in DB
            if output.get("violations"):
                logger.info(f"Job {job_id}: Storing {len(output['violations'])} violations in DB")
                store_violations_batch(output["violations"])

            # Persist adaptive thresholds
            if output.get("adaptive_thresholds"):
                save_threshold_state(output["adaptive_thresholds"])

            # Build lightweight summary for job result
            summary = generate_violation_summary(output)

            # ── Merge all_tracks + track_summaries ──────────────────────
            # video_pipeline may only put violating tracks in track_summaries.
            # all_tracks (if present) has the full set; merge them so the
            # dashboard shows every detected vehicle including clean ones.
            track_summaries = output.get("track_summaries", {})
            all_tracks_raw  = output.get("all_tracks", {})

            merged_tracks = {}
            for tid, t in all_tracks_raw.items():
                merged_tracks[tid] = t
            # Overlay richer violation fields from track_summaries
            for tid, t in track_summaries.items():
                if tid in merged_tracks:
                    merged_tracks[tid].update(t)
                else:
                    merged_tracks[tid] = t

            # Fallback: if pipeline doesn't emit all_tracks, just use track_summaries
            if not merged_tracks:
                merged_tracks = track_summaries

            logger.info(f"Job {job_id}: Final merged tracks: {len(merged_tracks)}")

            JOB_STORE[job_id] = {
                "status":              "completed",
                "summary":             summary,
                "track_summaries":     merged_tracks,
                "metadata":            output.get("metadata", {}),
                "temporal_stats":      output.get("temporal_stats", {}),
                "adaptive_thresholds": output.get("adaptive_thresholds", {}),
                "output_video_path":   output_video_path,
                "filename":            file.filename,
            }
            
            logger.info(f"Job {job_id}: Completed successfully")

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(f"Job {job_id}: FAILED with error: {error_msg}")
            logger.error(f"Job {job_id}: Traceback:\n{error_trace}")
            
            JOB_STORE[job_id] = {
                "status": "failed",
                "error":  error_msg,
                "trace":  error_trace,
                "filename": file.filename,
            }
        finally:
            # Cleanup temp video file
            if os.path.exists(video_path):
                try:
                    os.unlink(video_path)
                    logger.info(f"Job {job_id}: Cleaned up temp file {video_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Failed to cleanup temp file: {e}")

    threading.Thread(target=background_task, daemon=True).start()

    return {"status": "started", "job_id": job_id, "filename": file.filename}


# ─────────────────────────────────────────────
# JOB STATUS / RESULT
# ─────────────────────────────────────────────

@router.get("/job-status/{job_id}")
async def job_status(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "filename": job.get("filename"),
    }
    
    # Add progress info if available
    if "progress" in job:
        response["progress"] = job["progress"]
    if "total_frames" in job:
        response["total_frames"] = job["total_frames"]
        
    return response


@router.get("/job-result/{job_id}")
async def job_result(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] == "failed":
        # Include full error details in response
        logger.error(f"Returning failed job {job_id}: {job.get('error')}")
        logger.error(f"Traceback: {job.get('trace')}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": job.get("error", "Unknown error"),
                "trace": job.get("trace", ""),
                "filename": job.get("filename", ""),
            }
        )
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return job


@router.get("/job-video/{job_id}")
async def job_video(job_id: str):
    """Stream the annotated output video."""
    job = JOB_STORE.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Video not available")
    
    path = job.get("output_video_path")
    if not path or not os.path.exists(path):
        logger.error(f"Video file not found for job {job_id}: {path}")
        raise HTTPException(status_code=404, detail="Video file not found")
    
    logger.info(f"Serving video for job {job_id}: {path}")
    return FileResponse(path, media_type="video/mp4", filename=f"output_{job_id}.mp4")


# ─────────────────────────────────────────────
# VIOLATIONS (DATABASE READ)
# ─────────────────────────────────────────────

@router.get("/violations")
async def list_violations(
    limit:          int   = Query(200, ge=1, le=1000),
    offset:         int   = Query(0, ge=0),
    violation_type: Optional[str]  = Query(None),
    needs_review:   Optional[bool] = Query(None),
    min_quality:    float = Query(0.0, ge=0.0, le=1.0),
):
    """
    Read violations from the database.
    Supports filtering by type, review status, and minimum quality score.
    """
    rows = get_violations(
        limit=limit,
        offset=offset,
        violation_type=violation_type,
        needs_review=needs_review,
        min_quality=min_quality,
    )
    return {"violations": rows, "count": len(rows)}


@router.get("/violations/{violation_id}")
async def get_violation(violation_id: int):
    db_gen = get_db()
    conn   = next(db_gen)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM violations WHERE id = %s", (violation_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Violation not found")
            return dict(row)
    finally:
        db_gen.close()


# ─────────────────────────────────────────────
# TRACK SUMMARIES (per job)
# ─────────────────────────────────────────────

@router.get("/job-tracks/{job_id}")
async def job_tracks(job_id: str):
    """
    Return per-track summaries for the given job.
    Every unique vehicle detected — violating or clean — is included.
    """
    job = JOB_STORE.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Job not ready")

    track_summaries = job.get("track_summaries", {})
    # Sort by first_frame so tracks appear in temporal order
    tracks = sorted(
        track_summaries.values(),
        key=lambda t: t.get("first_frame", 0),
    )
    return {"job_id": job_id, "tracks": tracks, "count": len(tracks)}


# ─────────────────────────────────────────────
# ADAPTIVE THRESHOLDS
# ─────────────────────────────────────────────

@router.get("/thresholds")
async def get_thresholds():
    """Return current adaptive thresholds."""
    return load_threshold_state()


@router.post("/thresholds/reset")
async def reset_thresholds():
    """Reset thresholds to defaults."""
    defaults = {"hsrp": 0.50, "helmet": 0.40, "ocr_confidence": 0.60}
    save_threshold_state(defaults)
    return {"status": "reset", "thresholds": defaults}


# ─────────────────────────────────────────────
# LEGACY ENDPOINTS (backward compat)
# ─────────────────────────────────────────────

@router.get("/job-legacy-result/{job_id}")
async def legacy_result(job_id: str):
    """Kept for backward compatibility with old frontend code."""
    return await job_result(job_id)
