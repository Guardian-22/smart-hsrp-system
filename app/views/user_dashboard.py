"""
USER DASHBOARD
===============
- Upload video
- Track processing progress
- View annotated output video
- Per-track result table
"""

import streamlit as st
import time
import json
import pandas as pd
from utils.api_client import APIClient


def render(client: APIClient):
    st.title("Smart HSRP Monitoring")
    st.caption("Upload a traffic video to detect HSRP violations and helmet non-compliance.")

    # ── Upload form ──────────────────────────────
    with st.expander("⚙️ Processing Options", expanded=False):
        frame_skip = st.slider(
            "Frame skip (higher = faster, lower = more accurate)",
            min_value=1, max_value=5, value=1,   # ← default changed to 1
        )
        save_video = st.checkbox("Generate annotated output video", value=True)

        st.markdown("**Annotation Mode**")
        st.caption(
            "Control when annotation and OCR happen. "
            "If both are checked, annotation and OCR run on every frame."
        )
        annotate_violations    = st.checkbox("Annotate when violations occur",    value=True,  key="ann_viol")
        annotate_no_violations = st.checkbox("Annotate when no violations occur", value=False, key="ann_no_viol")

        # Derive OCR mode from annotation selection
        if annotate_violations and annotate_no_violations:
            ocr_mode = "always"
            st.info("🔵 Both checked → annotation + OCR always active on every frame.")
        elif annotate_violations:
            ocr_mode = "on_violation"
            st.info("🟡 OCR runs only when a violation is detected (cost-efficient).")
        elif annotate_no_violations:
            ocr_mode = "on_clean"
            st.info("🟢 OCR runs only when no violation is detected.")
        else:
            ocr_mode = "off"
            st.warning("⚪ Neither checked — no annotation will be drawn.")

    uploaded = st.file_uploader(
        "Upload video",
        type=["mp4", "avi", "mov", "mkv"],
        label_visibility="collapsed",
    )

    if not uploaded:
        _render_placeholder()
        return

    st.video(uploaded)

    col1, col2 = st.columns([1, 3])
    with col1:
        run = st.button("▶ Process Video", type="primary", use_container_width=True)

    if not run and "last_job_id" not in st.session_state:
        return

    # ── Submit job ───────────────────────────────
    if run:
        with st.spinner("Uploading…"):
            resp = client.upload_video(
                file_bytes=uploaded.read(),
                filename=uploaded.name,
                frame_skip=frame_skip,
                save_output_video=save_video,
                annotate_violations=annotate_violations,
                annotate_no_violations=annotate_no_violations,
                ocr_mode=ocr_mode,
            )
        if "job_id" not in resp:
            st.error(f"Upload failed: {resp}")
            return

        st.session_state["last_job_id"] = resp["job_id"]
        st.session_state["job_done"] = False

    job_id = st.session_state["last_job_id"]

    # ── Poll progress ─────────────────────────────
    if not st.session_state.get("job_done"):
        progress_bar = st.progress(0, text="Processing…")
        status_text  = st.empty()

        for pct in range(1, 101):
            status = client.get_job_status(job_id)
            if status["status"] == "completed":
                progress_bar.progress(100, text="Done!")
                st.session_state["job_done"] = True
                break
            if status["status"] == "failed":
                st.error(f"Processing failed: {status.get('error', '')}")
                return
            progress_bar.progress(pct, text=f"Processing… ({pct}%)")
            status_text.caption(f"Status: {status['status']}")
            time.sleep(2)

    # ── Load result ───────────────────────────────
    result = client.get_job_result(job_id)
    if not result:
        st.warning("No result available yet.")
        return

    # ── Summary cards ─────────────────────────────
    summary = result.get("summary", {})
    meta    = result.get("metadata", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Frames Processed",   meta.get("total_frames_processed", "—"))
    c2.metric("Avg FPS",             meta.get("avg_fps", "—"))
    c3.metric("Violations Found",    summary.get("total", 0))
    c4.metric("Needs Review",        summary.get("needs_review", 0))

    st.divider()

    # ── Download JSON Report ──────────────────────
    st.subheader("📥 Download Report")
    json_bytes = json.dumps(result, indent=2, default=str).encode("utf-8")
    st.download_button(
        label="⬇️ Download Full JSON Report",
        data=json_bytes,
        file_name=f"report_{job_id}.json",
        mime="application/json",
        help="Downloads the complete backend output for this job as a JSON file.",
    )

    st.divider()

    # ── Annotated video player ────────────────────
    if save_video:
        video_url = client.get_video_url(job_id)
        st.subheader("🎬 Annotated Output Video")
        st.caption("Grey = tracking  |  🟡 Yellow = violation predicted  |  🔴 Red = violation confirmed")

        import requests as _req
        vid_resp = _req.get(video_url, timeout=60)
        if vid_resp.status_code == 200:
            st.video(vid_resp.content)
        else:
            st.warning("Annotated video not available (may still be processing).")

    # ── Per-track table ───────────────────────────
    st.subheader("📋 Track-Level Results")
    st.caption(
        "Every vehicle detected — violating and clean. "
        "🔴 Red = violation stored  |  🟡 Yellow = needs review  |  ⬜ White = clean"
    )

    tracks_resp = client.get_job_tracks(job_id)
    tracks      = tracks_resp.get("tracks", [])

    if not tracks:
        st.info("No tracks found in this video.")
        return

    rows = []
    for t in tracks:
        vclass       = (t.get("vehicle_class") or "unknown").lower()
        is_two_wheel = vclass in ("motorcycle", "bicycle", "bike")

        # HSRP field
        hsrp_label = t.get("hsrp_label") or t.get("hsrp")
        if hsrp_label == "hsrp":
            hsrp_display = "✅ HSRP"
        elif hsrp_label in ("non_hsrp", "non hsrp"):
            hsrp_display = "❌ Non-HSRP"
        else:
            hsrp_display = "—"

        # Helmet field — only for two-wheelers
        if is_two_wheel:
            helmet_status = t.get("helmet_status") or t.get("helmet")
            if helmet_status == "HELMET":
                helmet_display = "✅ Helmet"
            elif helmet_status == "NO_HELMET":
                helmet_display = "❌ No Helmet"
            elif helmet_status == "UNCERTAIN":
                helmet_display = "❓ Uncertain"
            else:
                helmet_display = "—"
        else:
            helmet_display = "—"

        violation = _fmt_violation(t.get("violation_type"))
        stored    = t.get("should_store", False)
        review    = t.get("needs_review", False)

        rows.append({
            "Track ID":     t.get("track_id", "?"),
            "Vehicle":      vclass.title(),
            "Plate Number": t.get("plate_number") or t.get("vehicle_number") or "—",
            "HSRP":         hsrp_display,
            "Helmet":       helmet_display,
            "Violation":    violation if violation != "—" else "✅ Clean",
            "Confidence":   f"{t.get('violation_confidence', t.get('quality_score', 0)):.2f}",
            "Quality":      f"{t.get('quality_score', 0):.2f}",
            "Stored":       "✅ Yes" if stored else "—",
            "Review":       "⚠️ Yes" if review else "—",
            "Frames":       f"{t.get('first_frame', 0)}–{t.get('last_frame', 0)}",
        })

    df = pd.DataFrame(rows)

    def _row_style(row):
        if row["Stored"] == "✅ Yes" and row["Review"] == "⚠️ Yes":
            return ["background-color: #fff3cd; color: #856404"] * len(row)
        if row["Stored"] == "✅ Yes":
            return ["background-color: #f8d7da; color: #721c24"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
        height=450,
    )

    # By-type breakdown
    by_type = summary.get("by_type", {})
    if by_type:
        st.subheader("📊 Violation Breakdown")
        bdf = pd.DataFrame([
            {
                "Type":     k.replace("_", " ").title(),
                "Count":    v["count"],
                "Avg Confidence": f"{v['avg_conf']:.2f}",
            }
            for k, v in by_type.items()
        ])
        st.dataframe(bdf, use_container_width=True, hide_index=True)


# ── Helpers ───────────────────────────────────────

def _fmt_violation(vtype: str | None) -> str:
    if not vtype:
        return "—"
    return vtype.replace("_", " ").replace("non hsrp plate", "Non-HSRP Plate").title()


def _render_placeholder():
    st.markdown(
        """
        <div style='text-align:center; padding:3rem; color:#666;'>
          <h3>📂 No video uploaded</h3>
          <p>Upload a .mp4 / .avi / .mov file above to begin processing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
