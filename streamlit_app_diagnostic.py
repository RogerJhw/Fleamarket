
import streamlit as st

st.title("Streamlit Deployment Diagnostic")

st.write("✅ Base Streamlit app loaded successfully.")

# Step-by-step diagnostics
steps = [
    ("Importing qrcode", lambda: __import__('qrcode')),
    ("Importing PIL.Image", lambda: __import__('PIL.Image')),
    ("Importing dotenv", lambda: __import__('dotenv')),
    ("Importing algorand.asset.create_asset", lambda: __import__('algorand.asset', fromlist=['create_asset'])),
    ("Importing algorand.transactions.send_payment", lambda: __import__('algorand.transactions', fromlist=['send_payment'])),
    ("Importing algorand.contracts.compile_teal", lambda: __import__('algorand.contracts', fromlist=['compile_teal'])),
]

progress = 0
for description, func in steps:
    try:
        func()
        st.success(f"✅ {description}")
    except Exception as e:
        st.error(f"❌ {description} failed: {e}")
    progress += 1
    st.progress(progress / len(steps))

st.write("🧪 Diagnostic complete. Check errors above to isolate issues.")
