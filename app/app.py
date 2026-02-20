"""
SMART HSRP MONITORING SYSTEM
==============================
Streamlit frontend application.

Run with:
    streamlit run app/app.py
"""

import streamlit as st
from utils.api_client import APIClient
from views import user_dashboard, admin_dashboard

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Smart HSRP Monitor",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #eee !important; }
    .stButton>button { border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

if "client" not in st.session_state:
    st.session_state["client"] = APIClient(base_url="http://localhost:8000")
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "user"
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

client: APIClient = st.session_state["client"]

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🚦 Smart HSRP")
    st.markdown("---")

    if st.session_state["logged_in"]:
        st.success(f"👤 {st.session_state['user_email']}")
        st.caption(f"Role: {st.session_state['user_role'].title()}")
        st.markdown("---")

        pages = ["Detection"]
        if st.session_state["user_role"] == "admin":
            pages.append("🛡️ Admin")

        page = st.radio("Navigation", pages, label_visibility="collapsed")
        st.markdown("---")

        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_email"] = ""
            st.session_state["user_role"] = "user"
            client.token = None
            st.rerun()
    else:
        page = "login"
        st.info("Please login to continue.")


# ─────────────────────────────────────────────
# LOGIN / SIGNUP PAGE
# ─────────────────────────────────────────────

def render_auth():
    st.markdown("<h2 style='text-align:center'>🚦 Smart HSRP Monitoring</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:grey'>AI-Powered Traffic Violation Detection</p>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email    = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit   = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    result = client.login(email, password)
                    if result["success"]:
                        st.session_state["logged_in"]  = True
                        st.session_state["user_email"] = result.get("email", email)
                        st.session_state["user_role"]  = result.get("role", "user")
                        st.rerun()
                    else:
                        st.error(result.get("detail", "Login failed"))

        with tab_signup:
            with st.form("signup_form"):
                s_email    = st.text_input("Email", key="su_email")
                s_password = st.text_input("Password", type="password", key="su_pw")
                s_role     = st.selectbox("Role", ["user", "admin"])
                s_submit   = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if s_submit:
                if not s_email or not s_password:
                    st.error("Please fill in all fields.")
                else:
                    result = client.signup(s_email, s_password, s_role)
                    if result["success"]:
                        st.session_state["logged_in"]  = True
                        st.session_state["user_email"] = result.get("email", s_email)
                        st.session_state["user_role"]  = result.get("role", "user")
                        st.success("Account created!")
                        st.rerun()
                    else:
                        st.error(result.get("detail", "Signup failed"))


# ─────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────

if not st.session_state["logged_in"]:
    render_auth()
elif page == "Detection":
    user_dashboard.render(client)
elif page == "🛡️ Admin":
    if st.session_state["user_role"] == "admin":
        admin_dashboard.render(client)
    else:
        st.error("Access denied.")
