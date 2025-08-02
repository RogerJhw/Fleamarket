import os
from datetime import datetime
import logging

from supabase import create_client, Client

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Tokenized Fleamarket", layout="wide")

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Restore existing session if present
    session_obj = st.session_state.get("session")
    token = getattr(session_obj, "access_token", None)
    refresh = getattr(session_obj, "refresh_token", None)
    if token:
        try:
            supabase.auth.set_session(token, refresh or "")
            auth_user = supabase.auth.get_user()
            logging.info(
                "Authenticated user UID: %s",
                getattr(auth_user.user, "id", "unknown"),
            )
        except Exception as exc:
            logging.error("Failed to restore session: %s", exc)
else:
    st.error("Supabase credentials not configured")

# Default image used when an item has no valid image URL
PLACEHOLDER_IMAGE = "https://via.placeholder.com/200?text=No+Image"

logging.basicConfig(level=logging.INFO)


# def render_image(url: str) -> None:
#     """Safely display an image, falling back to a placeholder."""
#     if not url:
#         st.image(PLACEHOLDER_IMAGE, use_column_width=True)
#         st.caption("No image available")
#         return
#     try:
#         st.image(url, use_column_width=True)
#     except Exception as exc:
#         logging.warning("Failed to load image %s: %s", url, exc)
#         st.image(PLACEHOLDER_IMAGE, use_column_width=True)
#         st.caption("Image unavailable")

def render_image(url: str) -> None:
    """Safely display an image with rounded corners using HTML fallback."""
    display_url = url if url else PLACEHOLDER_IMAGE
    html = f"""
    <div style="text-align: center;">
        <img src="{display_url}" style="width: 100%; border-radius: 16px;" />
        <p style="color: gray;">{'No image available' if not url else ''}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# Session state initialization
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "selected_item" not in st.session_state:
    st.session_state["selected_item"] = None
if "selected_item_id" not in st.session_state:
    st.session_state["selected_item_id"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "session" not in st.session_state:
    st.session_state["session"] = None
if "show_create_form" not in st.session_state:
    st.session_state["show_create_form"] = False


def ensure_supabase_session() -> bool:
    """Ensure Supabase client is using the authenticated user's session."""
    if supabase is None:
        return False
    session_obj = st.session_state.get("session")
    token = getattr(session_obj, "access_token", None)
    refresh = getattr(session_obj, "refresh_token", None)
    if not token:
        st.error("Missing user session. Please log in again.")
        return False
    try:
        supabase.auth.set_session(token, refresh or "")
        auth_user = supabase.auth.get_user()
        logging.info("Authenticated user UID: %s", getattr(auth_user.user, "id", "unknown"))
        return True
    except Exception as exc:
        st.error("Failed to set user session")
        logging.error("Supabase set_session error: %s", exc)
        return False


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
            st.session_state["session"] = res.session
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Sign in failed: {e}")
    if cols[1].button("Sign Up"):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.session_state["user"] = res.user
            st.session_state["session"] = res.session
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
        render_image(item.get("image_url"))
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
    components.iframe("https://flea-wallet-widget.com", height=600, width=400)


import time

def create_listing_form():
    title = st.text_input("Item title")
    description = st.text_area("Description")
    price = st.number_input("Starting bid", min_value=0.00, step=0.01)
    uploaded_file = st.file_uploader("Image", type=["png", "jpg", "jpeg"])

    if st.button("List Item"):
        image_url = PLACEHOLDER_IMAGE  # default
        if uploaded_file:
            try:
                image_bytes = uploaded_file.read()
                file_name = f"{st.session_state['user'].id}_{int(time.time())}_{uploaded_file.name}"
                # Upload image to Supabase Storage
                supabase.storage.from_("images").upload(file_name, image_bytes)

                # Construct the public URL manually
                image_url = f"https://csojmedglbaofffdxasx.supabase.co/storage/v1/object/public/images/{file_name}"
            except Exception as exc:
                logging.error("Image upload failed: %s", exc)

        data = {
            "user_id": st.session_state["user"].id,
            "title": title,
            "description": description,
            "image_url": image_url,
            "current_bid": price,
        }
        supabase.table("items").insert(data).execute()
        st.success("Item listed")
        st.session_state["show_create_form"] = False
        st.experimental_rerun()


def user_listings_tab():
    st.header("Your Listings")
    if st.session_state.get("show_create_form"):
        create_listing_form()
    else:
        if st.button("Create New Listing"):
            st.session_state["show_create_form"] = True

    if supabase is None:
        st.error("Supabase not configured")
        return
    res = (
        supabase.table("items")
        .select("*")
        .eq("user_id", st.session_state["user"].id)
        .order("created_at", desc=True)
        .execute()
    )
    items = res.data or []
    if not items:
        st.info("You have not created any listings.")
    for idx, item in enumerate(items):
        render_item_card(idx, item)


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
    render_image(item.get("image_url"))
    st.write(item.get("description", ""))
    st.write(f"Current bid: {item.get('current_bid')}")
    bid_amt = st.number_input("Bid amount", min_value=float(item.get("current_bid", 0)), step=0.01)
    if st.button("Place Bid"):
        if not ensure_supabase_session():
            return
        if bid_amt > float(item.get("current_bid", 0)):
            supabase.table("items").update({"current_bid": bid_amt}).eq("id", item_id).execute()
            st.success("Bid placed")
            st.experimental_rerun()
        else:
            st.error("Bid must be greater than current bid")


# Top navigation using tabs
tab_labels = ["Marketplace", "Connect Wallet", "Your Listings", "Bid"]

if st.session_state.get("user") is not None:
    st.sidebar.write(f"Logged in as: {st.session_state['user'].email}")
if st.sidebar.button("Sign Out"):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.session_state["session"] = None
    st.experimental_rerun()

query_params = st.experimental_get_query_params()
active_tab = query_params.get("tab", ["Marketplace"])[0]
if active_tab not in tab_labels:
    active_tab = "Marketplace"

tab_marketplace, tab_wallet, tab_user_listings, tab_bid = st.tabs(tab_labels)

with tab_marketplace:
    marketplace_tab()

with tab_wallet:
    connect_wallet_tab()

with tab_user_listings:
    user_listings_tab()

with tab_bid:
    bid_tab()
