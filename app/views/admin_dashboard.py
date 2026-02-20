"""
ADMIN DASHBOARD
================
- Violations database viewer (read-only)
- Adaptive threshold monitor
- User management
- System stats
"""

import streamlit as st
import pandas as pd
from utils.api_client import APIClient


def render(client: APIClient):
    st.title("🛡️ Admin Dashboard")

    tab_violations, tab_thresholds, tab_users = st.tabs([
        "Violations Database",
        "Adaptive Thresholds",
        "Users",
    ])

    with tab_violations:
        _render_violations(client)

    with tab_thresholds:
        _render_thresholds(client)

    with tab_users:
        _render_users(client)


# ─────────────────────────────────────────────
# VIOLATIONS TAB
# ─────────────────────────────────────────────

def _render_violations(client: APIClient):
    st.subheader("Violations Database")
    st.caption("Read-only view of all stored violations.")

    # Filters
    with st.expander("Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            vtype = st.selectbox(
                "Violation Type",
                ["All", "non_hsrp_plate", "no_helmet"],
                index=0,
            )
        with col2:
            review_filter = st.selectbox(
                "Review Status",
                ["All", "Needs Review", "Auto-cleared"],
                index=0,
            )
        with col3:
            min_quality = st.slider("Min Quality Score", 0.0, 1.0, 0.0, 0.05)
        with col4:
            limit = st.number_input("Max rows", min_value=10, max_value=1000, value=200, step=10)

    # Map UI values to params
    vtype_param = None if vtype == "All" else vtype
    review_param = None
    if review_filter == "Needs Review":
        review_param = True
    elif review_filter == "Auto-cleared":
        review_param = False

    if st.button("🔄 Refresh", type="secondary"):
        st.cache_data.clear()

    data = client.get_violations(
        limit=int(limit),
        violation_type=vtype_param,
        needs_review=review_param,
        min_quality=min_quality,
    )
    violations = data.get("violations", [])

    # Summary metric strip
    total = data.get("count", len(violations))
    needs_r = sum(1 for v in violations if v.get("needs_manual_review"))
    auto_ok = total - needs_r

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Shown", total)
    m2.metric("Auto-cleared", auto_ok, delta_color="normal")
    m3.metric("Needs Review", needs_r, delta_color="inverse")

    if not violations:
        st.info("No violations found for the current filters.")
        return

    # Build display dataframe
    rows = []
    for v in violations:
        vclass       = (v.get("vehicle_class") or "unknown").lower()
        is_two_wheel = vclass in ("motorcycle", "bicycle", "bike")
        vtype        = v.get("violation_type") or ""

        # HSRP display: derive from violation type if not stored separately
        hsrp_raw = v.get("hsrp_label") or v.get("hsrp")
        if hsrp_raw == "hsrp":
            hsrp_display = "✅ HSRP"
        elif hsrp_raw in ("non_hsrp", "non hsrp"):
            hsrp_display = "❌ Non-HSRP"
        elif vtype == "non_hsrp_plate":
            hsrp_display = "❌ Non-HSRP"
        else:
            hsrp_display = "—"

        # Helmet display: derive from violation type if not stored separately
        if is_two_wheel:
            helmet_raw = v.get("helmet_status") or v.get("helmet")
            if helmet_raw == "HELMET":
                helmet_display = "✅ Helmet"
            elif helmet_raw == "NO_HELMET":
                helmet_display = "❌ No Helmet"
            elif vtype == "no_helmet":
                helmet_display = "❌ No Helmet"
            else:
                helmet_display = "—"
        else:
            helmet_display = "—"

        rows.append({
            "ID":           v.get("id"),
            "Track ID":     v.get("track_id") or "—",
            "Vehicle":      vclass.title(),
            "Plate Number": v.get("vehicle_number") or "—",
            "HSRP":         hsrp_display,
            "Helmet":       helmet_display,
            "Violation":    vtype.replace("_", " ").title() if vtype else "—",
            "Confidence":   f"{v.get('violation_confidence', 0):.2f}",
            "Quality":      f"{v.get('quality_score', 0):.2f}",
            "Stability":    f"{v.get('stability_score', 0):.2f}",
            "Pred. Led":    "✅" if v.get("prediction_preceded") else "❌",
            "Review":       "⚠️" if v.get("needs_manual_review") else "✅",
            "Frames":       f"{v.get('first_frame', 0)}–{v.get('last_frame', 0)}",
            "Stored At":    str(v.get("created_at", ""))[:19],
        })

    df = pd.DataFrame(rows)

    def _style_row(row):
        if row["Review"] == "⚠️":
            return ["background-color: #fff3cd; color: #856404"] * len(row)
        return ["background-color: #f8d7da; color: #721c24"] * len(row)

    st.dataframe(
        df.style.apply(_style_row, axis=1),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Export CSV",
        data=csv,
        file_name="violations_export.csv",
        mime="text/csv",
    )


# ─────────────────────────────────────────────
# ADAPTIVE THRESHOLDS TAB
# ─────────────────────────────────────────────

def _render_thresholds(client: APIClient):
    st.subheader("Adaptive Threshold Monitor")
    st.caption(
        "Thresholds are automatically learned from processed videos. "
        "Lower quality cameras trigger more conservative (higher) thresholds."
    )

    col_refresh, col_reset = st.columns([1, 1])
    with col_refresh:
        if st.button("🔄 Refresh Thresholds"):
            st.cache_data.clear()
    with col_reset:
        if st.button("↩️ Reset to Defaults", type="secondary"):
            result = client.reset_thresholds()
            st.success("Thresholds reset to defaults.")

    thresholds = client.get_thresholds()

    if not thresholds:
        st.info("No threshold data available yet. Process a video first.")
        return

    # Visual display
    labels = {
        "hsrp":           "HSRP Classification",
        "helmet":         "Helmet Detection",
        "ocr_confidence": "OCR Confidence",
    }
    defaults = {"hsrp": 0.50, "helmet": 0.40, "ocr_confidence": 0.60}

    for key, label in labels.items():
        val     = thresholds.get(key, defaults[key])
        default = defaults[key]
        delta   = round(val - default, 4)

        col_label, col_val, col_bar = st.columns([2, 1, 3])
        with col_label:
            st.write(f"**{label}**")
        with col_val:
            st.metric(
                label="",
                value=f"{val:.3f}",
                delta=f"{delta:+.3f} vs default",
                delta_color="inverse",
            )
        with col_bar:
            st.progress(val)

    st.divider()
    st.markdown(
        """
        **How it works:**
        - *Semi-supervised*: high-confidence predictions auto-labelled → thresholds adapt
        - *Quality-adjusted*: lower camera quality → slower threshold adaptation
        - *Momentum*: smooth changes, avoids threshold oscillation
        - Progress is persisted to `state/thresholds.json` and the database
        """
    )


# ─────────────────────────────────────────────
# USERS TAB
# ─────────────────────────────────────────────

def _render_users(client: APIClient):
    st.subheader("User Management")

    data = client.get_users()
    users = data.get("users", [])

    if not users:
        st.info("No users found or insufficient permissions.")
        return

    rows = [
        {
            "ID":         u.get("id"),
            "Email":      u.get("email"),
            "Role":       u.get("role", "user").title(),
            "Created At": str(u.get("created_at", ""))[:19],
        }
        for u in users
    ]

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )
