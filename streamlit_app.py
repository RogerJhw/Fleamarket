import streamlit as st
import uuid
import datetime
from io import BytesIO
import qrcode

st.set_page_config(page_title="Fleamarket", layout="wide")

if "auctions" not in st.session_state:
    st.session_state["auctions"] = {}

if "messages" not in st.session_state:
    st.session_state["messages"] = {}

if "username" not in st.session_state:
    st.session_state["username"] = ""

st.sidebar.title("Fleamarket")

st.session_state["username"] = st.sidebar.text_input(
    "Your name", st.session_state.get("username", ""), key="username_input"
)

section = st.sidebar.radio("Go to", ["Create Auction", "Fleamarket", "Messaging"])

now = datetime.datetime.utcnow()


def generate_qr(data: str) -> bytes:
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


if section == "Create Auction":
    st.header("List an item for auction")

    name = st.text_input("Item name")
    description = st.text_area("Description")
    images = st.file_uploader("Item images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    start_bid = st.number_input("Starting bid", min_value=0.0, step=1.0)
    max_bid = st.number_input("Max bid", min_value=0.0, step=1.0)
    duration_hours = st.number_input("Auction length in hours (min 24)", min_value=24, step=1)

    if st.button("Create auction"):
        if not st.session_state["username"]:
            st.error("Please enter your name in the sidebar first.")
        elif not name:
            st.error("Item name required")
        else:
            auction_id = str(uuid.uuid4())
            end_time = now + datetime.timedelta(hours=duration_hours)
            st.session_state["auctions"][auction_id] = {
                "seller": st.session_state["username"],
                "item_name": name,
                "description": description,
                "images": [file.getvalue() for file in images] if images else [],
                "starting_bid": start_bid,
                "max_bid": max_bid,
                "end_time": end_time,
                "bids": [],
                "closed": False,
                "winner": None,
                "payment_code": None,
                "payment_scanned": False,
            }
            st.success("Auction created")

elif section == "Fleamarket":
    st.header("Active auctions")
    to_remove = []
    for auction_id, auction in st.session_state["auctions"].items():
        if auction["closed"]:
            continue
        if now >= auction["end_time"]:
            auction["closed"] = True
            continue
        st.subheader(auction["item_name"])
        if auction["images"]:
            st.image(auction["images"], width=200)
        st.write(auction["description"])
        highest = auction["bids"][-1]["amount"] if auction["bids"] else auction["starting_bid"]
        st.write(f"Current bid: {highest}")
        st.write(f"Number of bids: {len(auction['bids'])}")
        bid_amount = st.number_input(
            f"Your bid for {auction['item_name']}", min_value=highest + 1, key=f"bid_{auction_id}"
        )
        if st.button("Place bid", key=f"btn_{auction_id}"):
            if not st.session_state["username"]:
                st.error("Enter your name in the sidebar first.")
            else:
                auction["bids"].append({"user": st.session_state["username"], "amount": bid_amount})
                if bid_amount >= auction["max_bid"]:
                    auction["closed"] = True
                    auction["winner"] = st.session_state["username"]
                    auction["payment_code"] = str(uuid.uuid4())
                    st.success("Bid placed and auction closed - you won!")
                st.experimental_rerun()

elif section == "Messaging":
    st.header("Messages")
    selectable = {
        a_id: a
        for a_id, a in st.session_state["auctions"].items()
        if a["closed"] and (a["seller"] == st.session_state["username"] or a.get("winner") == st.session_state["username"])
    }
    if not selectable:
        st.info("No auctions to message about.")
    else:
        selected = st.selectbox("Select auction", list(selectable.keys()), format_func=lambda x: selectable[x]["item_name"])
        auction = selectable[selected]
        st.write(f"Chat between {auction['seller']} and {auction.get('winner')}")
        msgs = st.session_state["messages"].setdefault(selected, [])
        for m in msgs:
            st.write(f"**{m['user']}**: {m['text']}")
        txt = st.text_input("Message", key="msg_input")
        if st.button("Send", key="send_btn"):
            if not st.session_state["username"]:
                st.error("Enter your name in the sidebar first.")
            elif not txt:
                st.error("Message cannot be empty")
            else:
                msgs.append({"user": st.session_state["username"], "text": txt})
                st.experimental_rerun()
        if auction.get("winner") and auction["payment_code"]:
            st.markdown("### Payment QR code (seller shows to buyer)")
            qr_bytes = generate_qr(auction["payment_code"])
            st.image(qr_bytes)
            if st.button("I have scanned the code", key=f"scan_{selected}"):
                auction["payment_scanned"] = True
                st.success("Payment confirmed")
