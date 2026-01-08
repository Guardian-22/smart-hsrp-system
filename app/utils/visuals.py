import cv2
import numpy as np

def draw_plate_overlays(image, plates):
    """
    Draw bounding boxes + labels on image
    """
    overlay = image.copy()

    for idx, plate in enumerate(plates):
        x1, y1, x2, y2 = plate["bbox"]

        color = (0, 255, 0) if plate["is_hsrp"] else (0, 0, 255)
        label = f"Plate {idx+1} | {'HSRP' if plate['is_hsrp'] else 'NON-HSRP'} ({plate['hsrp_confidence']:.2f})"

        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3)
        cv2.putText(
            overlay,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    return overlay
