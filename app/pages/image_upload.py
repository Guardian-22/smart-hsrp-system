import streamlit as st
import cv2
import numpy as np
from PIL import Image

from utils.api_client import trigger_img_detection, save_record
from utils.visuals import draw_plate_overlays


st.title("📷 Vehicle Image Analysis")

uploaded_file = st.file_uploader(
    "Upload a vehicle image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is None:
    st.info("Upload an image to begin analysis.")
    st.stop()


# ----------------------------
# Decode image EXACTLY like backend (NO EXIF rotation)
# ----------------------------
uploaded_file.seek(0)
file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
bgr_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

if bgr_img is None:
    st.error("Failed to decode image.")
    st.stop()

image_np = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)

# ----------------------------
# Display input image (visual only)
# ----------------------------
st.subheader("Input Image")
st.image(image_np, width="stretch")


# ----------------------------
# Run inference
# ----------------------------
if st.button("🚀 Run AI Analysis"):
    with st.spinner("Running detection pipeline..."):
        result = trigger_img_detection(
            uploaded_file.getvalue(),
            uploaded_file.name,
            uploaded_file.type
        )
        st.session_state["last_result"] = result


    if result is None:
        st.error("Backend did not return a response.")
        st.stop()

    # ----------------------------
    # Overlay visualization
    # ----------------------------
    st.subheader("Detection Overlay")

    plates = result.get("plates", [])
    overlay = draw_plate_overlays(bgr_img.copy(), plates)
    overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

    st.image(overlay_rgb, width="stretch")

    # ----------------------------
    # Summary badges
    # ----------------------------
    st.subheader("Violation Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Helmet Violation",
            "YES" if result.get("helmet_violation") else "NO",
            delta=f"{result.get('helmet_confidence', 0.0):.2f}"
        )

    with col2:
        any_hsrp_violation = any(p.get("hsrp_violation", False) for p in plates)
        st.metric(
            "HSRP Violation",
            "YES" if any_hsrp_violation else "NO"
        )

    # ----------------------------
    # Per-Plate Cards
    # ----------------------------
    st.subheader("Detected Plates")

    if not plates:
        st.info("No plates detected.")
    else:
        h, w = image_np.shape[:2]

        for idx, plate in enumerate(plates):
            with st.container():
                col1, col2 = st.columns([1, 3])

                # ----------------------------
                # Crop plate from SAME image YOLO saw
                # ----------------------------
                x1, y1, x2, y2 = plate["bbox"]

                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                crop = None
                if x2 > x1 and y2 > y1:
                    crop = image_np[y1:y2, x1:x2]

                with col1:
                    st.markdown(f"### Plate {idx + 1}")

                    if crop is not None:
                        st.image(
                            crop,
                            caption="Cropped Plate",
                            use_container_width=True
                        )

                    st.metric(
                        "HSRP",
                        "YES" if plate["is_hsrp"] else "NO",
                        delta=f"{plate['hsrp_confidence']:.2f}"
                    )

                with col2:
                    st.progress(plate["hsrp_confidence"])
                    st.markdown(
                        "🟢 **Compliant**"
                        if plate["is_hsrp"]
                        else "🔴 **Violation**"
                    )

                st.divider()

    st.divider()
    st.subheader("💾 Save Result")
    
    if "last_result" in st.session_state:
        if st.button("📥 Save in Records"):
            with st.spinner("Saving to database..."):
                save_resp = save_record(st.session_state["last_result"])
            if save_resp.get("error"):
                st.error(f"Save failed: {save_resp['error']}")
            else:
                st.success("✅ Record saved successfully!")
    else:
        st.info("Run analysis before saving.")

