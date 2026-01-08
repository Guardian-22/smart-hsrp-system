import streamlit as st
import pandas as pd
from utils.api_client import fetch_violations

st.set_page_config(page_title="Smart HSRP Dashboard", layout="wide")
st.title("📊 Smart HSRP Violations Dashboard")

# -----------------------------------
# Load once per session
# -----------------------------------
if "violations" not in st.session_state:
    with st.spinner("Fetching violations..."):
        st.session_state.violations = fetch_violations()

raw_data = st.session_state.violations

if not raw_data:
    st.info("No violations recorded yet.")
    st.stop()

# -----------------------------------
# Normalize API response
# -----------------------------------
events = []
plates = []

for item in raw_data:
    event_id = item.get("id")
    # Event-level data
    event = {
        "event_id": item.get("event_id"),
        "helmet_violation": item.get("helmet_violation", False),
        "helmet_confidence": item.get("helmet_confidence"),
        "helmet_count": item.get("helmet_count"),
        "image_path": item.get("image_path"),
        "created_at": item.get("created_at"),
    }
    events.append(event)

    # Plate-level data (can be multiple per event)
    for plate in item.get("plates", []):
        plates.append({
            "event_id": event_id,
            "plate_text": plate.get("ocr_text"),
            "is_hsrp": plate.get("is_hsrp"),
            "hsrp_confidence": plate.get("hsrp_confidence"),
            "ocr_confidence": plate.get("ocr_confidence"),
            "created_at": item.get("created_at"),
        })


events_df = pd.DataFrame(events)
plates_df = pd.DataFrame(plates)

# -----------------------------------
# KPIs
# -----------------------------------
st.subheader("📌 System Summary")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Events", len(events_df))

with c2:
    st.metric(
        "Helmet Violations",
        int(events_df["helmet_violation"].sum()) if not events_df.empty else 0
    )

with c3:
    st.metric("Total Plates", len(plates_df))

with c4:
    if not plates_df.empty and "is_hsrp" in plates_df:
        st.metric("HSRP Violations", int((~plates_df["is_hsrp"]).sum()))
    else:
        st.metric("HSRP Violations", 0)

st.divider()

# -----------------------------------
# Filters
# -----------------------------------
st.subheader("🔎 Filters")

col1, col2 = st.columns(2)

helmet_only = col1.checkbox("Helmet Violations Only")
hsrp_only = col2.checkbox("HSRP Violations Only")

filtered_events = events_df.copy()
filtered_plates = plates_df.copy()

if helmet_only:
    filtered_events = filtered_events[filtered_events["helmet_violation"]]
    filtered_plates = filtered_plates[
        filtered_plates["event_id"].isin(filtered_events["event_id"])
    ]

if hsrp_only and not filtered_plates.empty:
    filtered_plates = filtered_plates[~filtered_plates["is_hsrp"]]

# -----------------------------------
# Event Table
# -----------------------------------
st.subheader("🖼️ Image-Level Events")

st.dataframe(
    filtered_events,
    use_container_width=True
)

# -----------------------------------
# Plate Table
# -----------------------------------
st.subheader("🔍 Plate-Level Records")

if filtered_plates.empty:
    st.info("No plate records to display.")
else:
    st.dataframe(
        filtered_plates,
        use_container_width=True
    )

# -----------------------------------
# Debug (optional but recommended)
# -----------------------------------
with st.expander("🧪 Debug: Raw API Response"):
    st.json(raw_data)

with st.expander("🧪 Debug: DataFrame Columns"):
    st.write("Events columns:", list(events_df.columns))
    st.write("Plates columns:", list(plates_df.columns))
