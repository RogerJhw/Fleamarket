import os
from datetime import datetime
import logging
import json

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


def render_images(image_urls_in, *, height_px: int = 340, radius_px: int = 16):
    import json

    def coerce_urls(v):
        if not v: return []
        if isinstance(v, list): return [str(u).strip() for u in v if str(u).strip()]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list): return [str(u).strip() for u in arr if str(u).strip()]
                except Exception: pass
            if "," in s: return [p.strip() for p in s.split(",") if p.strip()]
            return [s]
        return []

    urls = coerce_urls(image_urls_in) or [PLACEHOLDER_IMAGE]

    slides = "\n".join(
        f'<div class="swiper-slide"><img src="{u}" alt="listing image"></div>'
        for u in urls
    )

    
    html = f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
    
    <style>
      /* Square viewport with rounded corners */
      .ratio-box {{
        aspect-ratio: 1 / 1;            /* change to 4 / 3 if you prefer */
        width: 100%;
        max-height: {height_px}px;       /* ensures we don't exceed iframe height */
        border-radius: {radius_px}px;
        overflow: hidden;
        position: relative;
      }}
      .ratio-box .mySwiper {{
        position: absolute;
        inset: 0;                        /* fill the ratio box */
        width: 100%;
        height: 100%;
      }}
    
      .mySwiper .swiper-wrapper {{ height: 100%; }}
      .mySwiper .swiper-slide {{
        width: 100% !important;
        height: 100%;
        display: flex; align-items: center; justify-content: center;
      }}
      .mySwiper img {{
        width: 100%;
        height: 100%;
        object-fit: cover;               /* uniform shape; no letterboxing */
        object-position: center;         /* tweak if faces are cropped */
        display: block;
      }}
    
      .mySwiper .swiper-pagination-bullets {{ bottom: 10px !important; }}
      .mySwiper .swiper-button-prev,
      .mySwiper .swiper-button-next {{ filter: drop-shadow(0 1px 2px rgba(0,0,0,.35)); }}
    </style>
    
    <div class="ratio-box">
      <div class="swiper mySwiper">
        <div class="swiper-wrapper">
          {slides}
        </div>
        <div class="swiper-button-prev"></div>
        <div class="swiper-button-next"></div>
        <div class="swiper-pagination"></div>
      </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    <script>
      const swiper = new Swiper('.mySwiper', {{
        slidesPerView: 1,
        centeredSlides: false,
        spaceBetween: 0,
        loop: false,
        watchOverflow: true,
        pagination: {{ el: '.swiper-pagination', clickable: true }},
        navigation: {{ nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' }}
      }});
    </script>
    """
    st.components.v1.html(html, height=height_px -  28, scrolling=False)  # +28 for dots

    # Height of the square viewport; parent column controls width.
    

# Session state initialization
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "user" not in st.session_state:
    st.session_state["user"] = None
if "session" not in st.session_state:
    st.session_state["session"] = None


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
    if cols[0].button("Sign In", key="sign_in_btn"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = res.user
            st.session_state["session"] = res.session
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Sign in failed: {e}")
    if cols[1].button("Sign Up", key="sign_up_btn"):
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
    if not getattr(user, "email_confirmed_at", None):
        st.warning("Please verify your email to continue using the app.")
        st.stop()

def render_item_card(idx: int, item: dict, show_delete: bool = False, prefix: str = ""):
    cols = st.columns([1, 1, 2])
    with cols[0]:
        render_images(item.get("image_urls"))
        bid_key = f"{prefix}_bid_input_{item['id']}"
        place_key = f"{prefix}_place_bid_{item['id']}"
        bid_amt = st.number_input(
            "Bid amount",
            min_value=float(item.get("current_bid", 0)),
            step=0.01,
            key=bid_key,
        )
        if st.button("Place Bid", key=place_key):
            if not ensure_supabase_session():
                return
            if bid_amt > float(item.get("current_bid", 0)):
                supabase.table("items").update({
                    "current_bid": bid_amt,
                    "highest_bidder": st.session_state["user"].id,
                }).eq("id", item["id"]).execute()
                st.success("Bid placed")
                st.experimental_rerun()
            else:
                st.error("Bid must be greater than current bid")
    with cols[1]:
        st.markdown(f"### {item.get('title')}")
        st.write(item.get("description", ""))
        st.write(f"Current bid: ${item.get('current_bid', 0):.2f}")
        st.write(f"Highest bidder: {item.get('highest_bidder', 'None')}")
        if show_delete:
            if st.button("Delete", key=f"delete_btn_{item['id']}"):
                supabase.table("items").delete().eq("id", item["id"]).execute()
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
        render_item_card(idx, item, show_delete=False, prefix="market")



def connect_wallet_tab():
    st.header("Connect Wallet")
    components.iframe("https://flea-wallet-widget.com", height=600, width=400)


import time

def create_listing_form():
    title = st.text_input("Item title")
    description = st.text_area("Description")
    price = st.number_input("Starting bid", min_value=0.00, step=0.01)
    uploaded_files = st.file_uploader(
        "Images (up to 3)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    # Limit uploads to 3
    if uploaded_files and len(uploaded_files) > 3:
        st.error("You can only upload up to 3 images.")
        return

    # Show image preview
    if uploaded_files:
        st.write("Preview:")
        for f in uploaded_files:
            st.image(f, use_column_width=True)

    if st.button("List Item", key="list_item_btn"):
        image_urls = []
        for uploaded_file in uploaded_files or []:
            try:
                image_bytes = uploaded_file.read()
                file_name = f"{st.session_state['user'].id}_{int(time.time())}_{uploaded_file.name}"
                supabase.storage.from_("images").upload(file_name, image_bytes)
                public_url = (
                    f"https://csojmedglbaofffdxasx.supabase.co/storage/v1/object/public/images/{file_name}"
                )
                image_urls.append(public_url)
            except Exception as exc:
                logging.error("Image upload failed: %s", exc)

        data = {
            "user_id": st.session_state["user"].id,
            "title": title,
            "description": description,
            "image_urls": json.dumps(image_urls),
            "current_bid": price,
            "highest_bidder": None,
        }
        supabase.table("items").insert(data).execute()
        st.success("Item listed")
        st.session_state["show_create_form"] = False
        st.experimental_rerun()


def user_listings_tab():
    if "show_create_form" not in st.session_state:
        st.session_state["show_create_form"] = False
    st.header("Your Listings")
    if st.button("Create New Listing", key="create_listing_btn"):
        st.session_state["show_create_form"] = True

    if st.session_state["show_create_form"]:
        create_listing_form()
        st.divider()

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
        render_item_card(idx, item, show_delete=True, prefix="user")


def my_bids_tab():
    st.header("My Bids")
    if supabase is None:
        st.error("Supabase not configured")
        return
    user_id = st.session_state["user"].id
    res = supabase.table("items").select("*").eq("highest_bidder", user_id).execute()
    items = res.data or []
    if not items:
        st.info("You are not currently the highest bidder on any listings.")
    for idx, item in enumerate(items):
        render_item_card(idx, item, show_delete=False, prefix="mybids")



# Top navigation using tabs
tab_labels = ["Marketplace", "Connect Wallet", "Your Listings", "My Bids"]

if st.session_state.get("user") is not None:
    st.sidebar.write(f"Logged in as: {st.session_state['user'].email}")
if st.sidebar.button("Sign Out", key="sign_out_btn"):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.session_state["session"] = None
    st.experimental_rerun()

query_params = st.experimental_get_query_params()
active_tab = query_params.get("tab", ["Marketplace"])[0]
if active_tab not in tab_labels:
    active_tab = "Marketplace"

tab_marketplace, tab_wallet, tab_user_listings, tab_my_bids = st.tabs(tab_labels)

with tab_marketplace:
    marketplace_tab()

with tab_wallet:
    connect_wallet_tab()

with tab_user_listings:
    user_listings_tab()

with tab_my_bids:
    my_bids_tab()
