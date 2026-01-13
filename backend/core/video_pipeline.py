import cv2

from backend.services.video_reader import read_video
from backend.utils.fps_controller import TimeBasedFPSController
from backend.services.vehicle_tracker import VehicleTracker
from backend.services.cropper import crop_rois

from backend.models.vehicle_detector import VehicleDetector
from backend.core.pipeline import run_pipeline


def process_video(video_path, target_fps=8):
    """
    Orchestrates full video processing pipeline.
    """

    # ------------------------
    # Initialize components
    # ------------------------
    fps_controller = TimeBasedFPSController(target_fps=target_fps)
    vehicle_detector = VehicleDetector()
    vehicle_tracker = VehicleTracker()

    results = {}

    # ------------------------
    # Frame loop
    # ------------------------
    for frame_id, frame in read_video(video_path):

        # FPS control
        if not fps_controller.should_process():
            continue

        # Vehicle detection
        detections = vehicle_detector.detect(frame)

        if not detections:
            continue

        # Vehicle tracking
        tracks = vehicle_tracker.update(
            detections=detections,
            frame=frame
        )

        if not tracks:
            continue

        # Crop vehicle ROIs
        for track in tracks:
            track_id = track["track_id"]
            bbox = track["bbox"]

            vehicle_crop = crop_rois(frame, [bbox])
            if not vehicle_crop:
                continue

            vehicle_crop = vehicle_crop[0]

            # Reuse existing image pipeline
            output = run_pipeline(
                vehicle_crop,
                image_path=f"{video_path}:frame_{frame_id}:track_{track_id}",
                force_save=False
            )

            results.setdefault(track_id, {
                "track_id": track_id,
                "events": []
            })

            results[track_id]["events"].append({
                "frame_id": frame_id,
                "source_ref": f"{video_path}:frame_{frame_id}:track_{track_id}",
                "pipeline_output": output
            })


    return results
