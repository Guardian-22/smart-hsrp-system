import streamlit as st

st.set_page_config(
    page_title="Smart HSRP System",
    layout="wide"
)

st.title("🚦 Smart HSRP Violation Detection System")

st.sidebar.info(
    "📌 Use the pages on the left to upload images or view violations."
)

st.markdown("""
This system detects:
- 🪖 Helmet violations
- 🔢 HSRP number plate compliance
""")
