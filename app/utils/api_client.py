"""
API Client
===========
Handles all communication between the Streamlit frontend and the FastAPI backend.
"""

import requests
import time
from typing import Optional, Dict, Any


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ── Auth ──────────────────────────────────────
    def login(self, email: str, password: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            return {"success": True, **data}
        return {"success": False, "detail": resp.json().get("detail", "Login failed")}

    def signup(self, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/signup",
            json={"email": email, "password": password, "role": role},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            return {"success": True, **data}
        return {"success": False, "detail": resp.json().get("detail", "Signup failed")}

    # ── Video processing ──────────────────────────
    def upload_video(
        self,
        file_bytes: bytes,
        filename: str,
        frame_skip: int = 1,
        save_output_video: bool = True,
        annotate_violations: bool = True,
        annotate_no_violations: bool = False,
        ocr_mode: str = "on_violation",
    ) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/api/process-video",
            files={"file": (filename, file_bytes, "video/mp4")},
            data={
                "frame_skip": str(frame_skip),
                "save_output_video": str(save_output_video).lower(),
                "annotate_violations": str(annotate_violations).lower(),
                "annotate_no_violations": str(annotate_no_violations).lower(),
                "ocr_mode": ocr_mode,
            },
            timeout=30,
        )
        return resp.json()

    def poll_job(self, job_id: str, interval: float = 2.0) -> Dict[str, Any]:
        """Poll until job completes or times out."""
        
        while True:
            status = self.get_job_status(job_id)
            if status.get("status") in ("completed", "failed"):
                return status
            time.sleep(interval)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/api/job-status/{job_id}", timeout=10)
        return resp.json()

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/api/job-result/{job_id}", timeout=10)
        return resp.json() if resp.status_code == 200 else {}

    def get_job_tracks(self, job_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/api/job-tracks/{job_id}", timeout=10)
        return resp.json() if resp.status_code == 200 else {}

    def get_video_url(self, job_id: str) -> str:
        return f"{self.base_url}/api/job-video/{job_id}"

    # ── Violations DB ─────────────────────────────
    def get_violations(
        self,
        limit: int = 200,
        violation_type: Optional[str] = None,
        needs_review: Optional[bool] = None,
        min_quality: float = 0.0,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": limit,
            "min_quality": min_quality,
        }
        if violation_type:
            params["violation_type"] = violation_type
        if needs_review is not None:
            params["needs_review"] = needs_review

        resp = requests.get(
            f"{self.base_url}/api/violations",
            params=params,
            timeout=10,
        )
        return resp.json() if resp.status_code == 200 else {"violations": [], "count": 0}

    # ── Thresholds ────────────────────────────────
    def get_thresholds(self) -> Dict[str, float]:
        resp = requests.get(f"{self.base_url}/api/thresholds", timeout=5)
        return resp.json() if resp.status_code == 200 else {}

    def reset_thresholds(self) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/api/thresholds/reset", timeout=5)
        return resp.json() if resp.status_code == 200 else {}

    # ── Users (admin) ─────────────────────────────
    def get_users(self) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/users",
            params={"token": self.token},
            timeout=10,
        )
        return resp.json() if resp.status_code == 200 else {}
