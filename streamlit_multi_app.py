
import os
from datetime import datetime

from supabase import create_client, Client

import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Tokenized Fleamarket", layout="wide")

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Supabase credentials not configured")

# Session state initialization
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "selected_item" not in st.session_state:
    st.session_state["selected_item"] = None
if "selected_item_id" not in st.session_state:
    st.session_state["selected_item_id"] = None
if "wallet" not in st.session_state:
    st.session_state["wallet"] = None
if "wallet_address" not in st.session_state:
    st.session_state["wallet_address"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None


def connect_wallet() -> str | None:
    """Open the Pera Wallet connect modal and return the selected address."""
    if st.session_state.get("wallet_address"):
        return st.session_state["wallet_address"]

    js = """
    async function connectPera() {
        try {
            if (typeof window.PeraWalletConnect === 'undefined') {
                await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = 'https://unpkg.com/@perawallet/connect';
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                });
            }
            const pera = new PeraWalletConnect();
            const accounts = await pera.connect();
            return accounts[0] ?? '';
        } catch (e) {
            return '';
        }
    }
    return await connectPera();
    """

    addr = st_javascript(js, key="connect_wallet")
    if addr:
        st.session_state["wallet_address"] = addr
        st.session_state["wallet"] = addr  # backward compatibility
        user = st.session_state.get("user")
        if supabase is not None and user is not None:
            try:
                supabase.table("wallets").upsert({"user_id": user.id, "address": addr}).execute()
            except Exception:
                pass
    return addr or None


def login_page():
    """Render login/sign-up form using Supabase authentication."""
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    cols = st.columns(2)
    if cols[0].button("Sign In"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = res.user
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Sign in failed: {e}")
    if cols[1].button("Sign Up"):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.session_state["user"] = res.user
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Sign up failed: {e}")

if st.session_state.get("user") is None:
    login_page()
    st.stop()
else:
    user = st.session_state["user"]
    if getattr(user, "email_confirmed_at", None):
        st.success("Email verified")

def render_item_card(idx: int, item: dict):
    cols = st.columns([1, 2])
    with cols[0]:
        if item.get("image_url"):
            st.image(item["image_url"], use_column_width=True)
    with cols[1]:
        st.subheader(item.get("title"))
        st.write(item.get("description", ""))
        st.write(f"Current bid: {item.get('current_bid')}")
        if st.button("View", key=f"bid_{idx}"):
            st.session_state["selected_item_id"] = item["id"]
            st.experimental_set_query_params(tab="Bid")
            st.experimental_rerun()

def marketplace_tab():
    st.header("Marketplace")
    if supabase is None:
        st.error("Supabase not configured")
        return
    res = supabase.table("items").select("*").order("created_at", desc=True).execute()
    items = res.data or []
    if not items:
        st.info("No items listed yet.")
    for idx, item in enumerate(items):
        render_item_card(idx, item)

def connect_wallet_tab():
    st.header("Connect Wallet")

    components.iframe("public/pera_wallet_connector.html", height=300)

    if st.session_state.get("wallet_address"):
        st.success(f"Wallet connected: {st.session_state['wallet_address']}")

    js = """
    await new Promise((resolve) => {
        const handler = (event) => {
            const data = event.data;
            if (data && data.wallet) {
                window.removeEventListener('message', handler);
                resolve(data.wallet);
            }
        };
        window.addEventListener('message', handler);
    });
    """

    addr = st_javascript(js, key="wallet_listener")
    if isinstance(addr, str) and addr:
        st.session_state["wallet_address"] = addr
        st.session_state["wallet"] = addr  # backward compatibility
        user = st.session_state.get("user")
        if supabase is not None and user is not None:
            try:
                supabase.table("wallets").upsert({"user_id": user.id, "address": addr}).execute()
            except Exception:
                pass
        st.experimental_rerun()

def list_item_tab():
    st.header("List an Item")
    with st.form("list_form"):
        title = st.text_input("Item title")
        description = st.text_area("Description")
        price = st.number_input("Starting bid", min_value=0.0, step=0.01)
        uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
        submit = st.form_submit_button("List Item")
    if submit:
        if supabase is None or st.session_state.get("user") is None:
            st.error("Please log in")
            return
        if not title:
            st.error("Please provide a title")
            return
        image_url = None
        if uploaded:
            file_bytes = uploaded.read()
            fname = f"{st.session_state['user'].id}_{int(datetime.utcnow().timestamp())}_{uploaded.name}"
            try:
                supabase.storage.from_("images").upload(fname, file_bytes, {"upsert": True})
                image_url = supabase.storage.from_("images").get_public_url(fname).get("publicUrl")
            except Exception:
                st.warning("Failed to upload image")
        data = {
            "user_id": st.session_state["user"].id,
            "title": title,
            "description": description,
            "image_url": image_url,
            "current_bid": price,
        }
        supabase.table("items").insert(data).execute()
        st.success("Item listed")
        st.experimental_rerun()

def bid_tab():
    item_id = st.session_state.get("selected_item_id")
    if not item_id:
        st.warning("No item selected. Please choose one from the Marketplace.")
        return
    res = supabase.table("items").select("*").eq("id", item_id).single().execute()
    item = res.data
    if not item:
        st.error("Item not found")
        return
    st.header(item.get("title"))
    if item.get("image_url"):
        st.image(item["image_url"])
    st.write(item.get("description", ""))
    st.write(f"Current bid: {item.get('current_bid')}")
    bid_amt = st.number_input("Bid amount", min_value=float(item.get("current_bid", 0)), step=0.01)
    if st.button("Place Bid"):
        if bid_amt > float(item.get("current_bid", 0)):
            supabase.table("items").update({"current_bid": bid_amt}).eq("id", item_id).execute()
            st.success("Bid placed")
            st.experimental_rerun()
        else:
            st.error("Bid must be greater than current bid")

# Top navigation using tabs
tab_labels = ["Marketplace", "Connect Wallet", "List Item", "Bid"]

if st.session_state.get("user") is not None:
    st.sidebar.write(f"Logged in as: {st.session_state['user'].email}")
if st.sidebar.button("Sign Out"):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.experimental_rerun()

query_params = st.experimental_get_query_params()
active_tab = query_params.get("tab", ["Marketplace"])[0]
if active_tab not in tab_labels:
    active_tab = "Marketplace"

tab_marketplace, tab_wallet, tab_list, tab_bid = st.tabs(tab_labels)

with tab_marketplace:
    marketplace_tab()

with tab_wallet:
    connect_wallet_tab()

with tab_list:
    list_item_tab()

with tab_bid:
    bid_tab()
