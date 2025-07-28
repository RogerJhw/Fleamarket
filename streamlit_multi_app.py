import base64
from io import BytesIO

import streamlit as st
from PIL import Image
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Tokenized Fleamarket", layout="wide")

# Session state initialization
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "selected_item" not in st.session_state:
    st.session_state["selected_item"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Marketplace"
if "nav" not in st.session_state:
    st.session_state["nav"] = "Marketplace"
if "wallet" not in st.session_state:
    st.session_state["wallet"] = None

def connect_wallet():
    """Connect to Pera wallet via WalletConnect."""
    js = """
    const connect = async () => {
        if (!window.PeraWalletConnect) {
            await import('https://perawallet.app/pera-wallet-connect.js');
        }
        const pera = new window.PeraWalletConnect();
        const accounts = await pera.connect();
        return accounts[0] || '';
    };
    return await connect();
    """
    addr = st_javascript(js, key="connect")
    if addr:
        st.session_state["wallet"] = addr
    return addr

def render_item_card(idx: int, item: dict):
    cols = st.columns([1, 2])
    with cols[0]:
        st.image(item["image"], use_column_width=True)
    with cols[1]:
        st.subheader(item["title"])
        st.write(f"Current bid: {item['price']}")
        if st.button("Bid", key=f"bid_{idx}"):
            st.session_state["selected_item"] = idx
            st.session_state["page"] = "Bid"
            st.experimental_rerun()

def marketplace_tab():
    st.header("Marketplace")
    if not st.session_state["listings"]:
        st.info("No items listed yet.")
    for idx, item in enumerate(st.session_state["listings"]):
        render_item_card(idx, item)

def connect_wallet_tab():
    st.header("Connect Wallet")
    if st.button("Connect Pera Wallet"):
        connect_wallet()
    if st.session_state.get("wallet"):
        st.success(f"Connected address: {st.session_state['wallet']}")

def list_item_tab():
    st.header("List an Item")
    with st.form("list_form"):
        title = st.text_input("Item title")
        price = st.number_input("Starting bid", min_value=0.0, step=0.01)
        uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
        submit = st.form_submit_button("List Item")
    if submit:
        if not uploaded:
            st.error("Please upload an image")
        else:
            image_bytes = uploaded.read()
            st.session_state["listings"].append({
                "title": title,
                "price": price,
                "image": image_bytes,
            })
            st.success("Item listed")

def bid_tab():
    idx = st.session_state.get("selected_item")
    if idx is None or idx >= len(st.session_state["listings"]):
        st.warning("No item selected. Please choose one from the Marketplace.")
        return
    item = st.session_state["listings"][idx]
    st.header(item["title"])
    st.image(item["image"])
    st.write(f"Current bid: {item['price']}")
    bid_amt = st.number_input("Bid amount", min_value=0.0, step=0.01)
    if st.button("Place Bid"):
        if bid_amt > item["price"]:
            item["price"] = bid_amt
            st.success("Bid placed")
        else:
            st.error("Bid must be greater than current bid")

# Top navigation
page_options = ["Marketplace", "Connect Wallet", "List Item"]

prev_page = st.session_state.get("page", "Marketplace")
prev_nav = st.session_state.get("nav", "Marketplace")
nav_index = page_options.index(prev_nav) if prev_nav in page_options else 0

nav_selection = st.radio(
    "Navigation",
    page_options,
    horizontal=True,
    index=nav_index,
    key="nav",
)

if prev_page == "Bid":
    if nav_selection != prev_nav:
        st.session_state["page"] = nav_selection
        st.experimental_rerun()
else:
    if nav_selection != prev_page:
        st.session_state["page"] = nav_selection
        st.experimental_rerun()

page = st.session_state.get("page", "Marketplace")

if page == "Marketplace":
    marketplace_tab()
elif page == "Connect Wallet":
    connect_wallet_tab()
elif page == "List Item":
    list_item_tab()
elif page == "Bid":
    bid_tab()
