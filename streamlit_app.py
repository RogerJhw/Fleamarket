import base64
import io
import time

import filetype
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Fleamarket", layout="wide")

# In-memory storage for listings
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "last_listing" not in st.session_state:
    st.session_state["last_listing"] = 0.0

st.title("Fleamarket")
components.iframe("https://flea-wallet-widget.com", height=600, width=400)

st.header("List an Item")
with st.form("list_form"):
    name = st.text_input("Name")
    desc = st.text_area("Description")
    price = st.number_input("Price (Algos)", min_value=0.0, step=0.01)
    uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
    submit = st.form_submit_button("Create Listing")
    if submit:
        if time.time() - st.session_state["last_listing"] < 30:
            st.error("Please wait before creating another listing")
        elif not uploaded or not uploaded.type.startswith("image/"):
            st.error("Upload a valid image")
        else:
            img_data = uploaded.read()
            kind = filetype.guess(img_data)
            if kind is None or not kind.mime.startswith("image/"):
                st.error("Invalid image format")
            else:
                try:
                    img = Image.open(io.BytesIO(img_data))
                    img.verify()
                except Exception:
                    st.error("Invalid image file")
                else:
                    listing = {
                        "name": name,
                        "description": desc,
                        "price": int(price * 1_000_000),
                        "image": base64.b64encode(img_data).decode(),
                        "sold": False,
                    }
                    st.session_state["listings"].append(listing)
                    st.session_state["last_listing"] = time.time()
                    st.success("Listing created")

st.header("Available Items")
for item in st.session_state["listings"]:
    st.subheader(item["name"])
    st.write(item["description"])
    st.write(f"Price: {item['price']/1_000_000} Algos")
    st.image(io.BytesIO(base64.b64decode(item["image"])))
    if not item.get("sold"):
        if st.button(f"Mark {item['name']} as Sold", key=item["name"]):
            item["sold"] = True
            st.success("Marked as sold")
    else:
        st.warning("Item already sold")
