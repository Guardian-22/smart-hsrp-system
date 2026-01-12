from deep_sort_realtime.deepsort_tracker import DeepSort


class VehicleTracker:
    def __init__(
        self,
        max_age=60,
        n_init=5,
        max_cosine_distance=0.2,
        max_iou_distance=0.7        # VERY IMPORTANT
    ):
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            max_cosine_distance=max_cosine_distance,
            max_iou_distance=max_iou_distance
        )

    def update(self, detections, frame):
        """
        Input:
            detections: List[dict]
            [
                {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float,
                    "class": str
                }
            ]
            frame: np.ndarray

        Output:
            List[dict]
            [
                {
                    "track_id": int,
                    "bbox": [x1, y1, x2, y2],
                    "class": str
                }
            ]
        """

        deep_sort_inputs = []

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            cls = det["class"]

            w = x2 - x1
            h = y2 - y1

            if w <= 0 or h <= 0 or conf < 0.4:
                continue

            # DeepSORT expects: ([x, y, w, h], confidence, class)
            deep_sort_inputs.append(
                ([x1, y1, w, h], conf, cls)
            )

        tracks = self.tracker.update_tracks(
            deep_sort_inputs,
            frame=frame
        )

        output_tracks = []

        for track in tracks:
            if not track.is_confirmed():
                continue

            x1, y1, x2, y2 = map(int, track.to_ltrb())

            output_tracks.append({
                "track_id": track.track_id,
                "bbox": [x1, y1, x2, y2],
                "class": track.get_det_class()
            })

        return output_tracks
