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
if "tab" not in st.session_state:
    st.session_state["tab"] = "Marketplace"
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
            st.session_state["tab"] = "Bid"

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
        st.info("Select an item from the Marketplace to bid on.")
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

# Sidebar navigation
selection = st.sidebar.radio(
    "Navigation",
    ["Marketplace", "Connect Wallet", "List Item", "Bid"],
    index=["Marketplace", "Connect Wallet", "List Item", "Bid"].index(st.session_state.get("tab", "Marketplace")),
)

st.session_state["tab"] = selection

if selection == "Marketplace":
    marketplace_tab()
elif selection == "Connect Wallet":
    connect_wallet_tab()
elif selection == "List Item":
    list_item_tab()
elif selection == "Bid":
    bid_tab()
