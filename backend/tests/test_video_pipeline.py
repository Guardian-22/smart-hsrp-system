""" Current Issue  
The problem is that your detector is losing the vehicle for a moment,
 and your tracker isn't patient enough to wait for it to come back. """

import cv2
from backend.services.video_reader import read_video
from backend.utils.fps_controller import TimeBasedFPSController
from backend.services.vehicle_tracker import VehicleTracker
from backend.services.cropper import crop_rois
from backend.models.vehicle_detector import VehicleDetector
from backend.core.pipeline import run_pipeline

def test_video_pipeline():
    video_path = "test_videos/test_traffic2.mp4"

    fps_controller = TimeBasedFPSController(target_fps=5)  # mimic low FPS
    vehicle_detector = VehicleDetector()
    vehicle_tracker = VehicleTracker()

    results = {}

    for frame_id, frame in read_video(video_path):
        if not fps_controller.should_process():
            continue

        # Vehicle detection
        detections = vehicle_detector.detect(frame)

        if not detections:
            continue

        # Tracking
        tracks = vehicle_tracker.update(detections=detections, frame=frame)

        for track in tracks:
            track_id = track["track_id"]
            bbox = track["bbox"]

            vehicle_crop = crop_rois(frame, [bbox])[0]

            # Send ROI to image pipeline
            output = run_pipeline(
                vehicle_crop,
                image_path=f"{video_path}:frame_{frame_id}:track_{track_id}",
                force_save=False
            )

            results.setdefault(track_id, []).append({
                "frame_id": frame_id,
                "output": output
            })

        # ✅ Print track info for debug
        print(f"Frame {frame_id} Tracks: {[t['track_id'] for t in tracks]}")

    # Final results summary
    print("\n=== TRACK SUMMARY ===")
    for track_id, frames in results.items():
        print(f"Track {track_id}: frames { [f['frame_id'] for f in frames] }")



