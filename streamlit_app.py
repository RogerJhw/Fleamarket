import streamlit as st

try:
    import qrcode  # noqa: F401  # placeholder for optional dependency
except Exception:
    qrcode = None

st.set_page_config(page_title="Fleamarket", layout="wide")

st.title("Hello, world!")
