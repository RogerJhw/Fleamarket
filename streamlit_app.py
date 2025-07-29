import base64
import filetype
from PIL import Image
import io
import json
import os
import time

import streamlit as st
from algosdk import encoding, transaction
from algorand_client import algod_client
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Fleamarket", layout="wide")

# In-memory storage for listings
if "listings" not in st.session_state:
    st.session_state["listings"] = []
if "wallet" not in st.session_state:
    st.session_state["wallet"] = None
if "last_listing" not in st.session_state:
    st.session_state["last_listing"] = 0.0


def connect_wallet() -> str | None:
    """Connect to Pera Wallet via WalletConnect and return address."""
    js_code = """
    const load = async () => {
        if (!window.PeraWalletConnect) {
            await import('https://cdn.jsdelivr.net/npm/@perawallet/connect@latest/dist/perawallet-connect.min.js');
        }
        const pera = new window.PeraWalletConnect();
        const accounts = await pera.connect();
        return accounts[0] || '';
    };
    return await load();
    """
    addr = st_javascript(js_code, key="connect")
    if addr:
        st.session_state["wallet"] = addr
        st.success(f"Connected wallet: {addr}")
    return addr or None


def mint_asa(name: str, description: str, price: int, image: bytes) -> int | None:
    """Mint an ASA representing the item and return its ID."""
    if algod_client is None or st.session_state.get("wallet") is None:
        st.error("Algod client not configured or wallet not connected")
        return None
    params = algod_client.suggested_params()
    addr = st.session_state["wallet"]
    txn = transaction.AssetCreateTxn(
        sender=addr,
        sp=params,
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name=name[:8].upper(),
        asset_name=name,
        manager=addr,
        reserve=addr,
        freeze=addr,
        clawback=addr,
        note=description.encode(),
    )
    tx_json = json.dumps(transaction.transaction_to_dict(txn))
    js = f"""
    const sign = async () => {{
        if (!window.PeraWalletConnect) {{
            await import('https://cdn.jsdelivr.net/npm/@perawallet/connect@latest/dist/perawallet-connect.min.js');
        }}
        const pera = new window.PeraWalletConnect();
        const blob = new Uint8Array(atob('{txn.signing_msg()}').split('').map(c=>c.charCodeAt(0)));
        const { signedTx } = await pera.signTransaction([{{ txn: {tx_json} }}]);
        return btoa(String.fromCharCode.apply(null, signedTx));
    }};
    return await sign();
    """
    signed = st_javascript(js, key="sign_create")
    if not signed:
        st.error("Transaction not signed")
        return None
    st.info("Sending transaction to network...")
    txid = algod_client.send_raw_transaction(base64.b64decode(signed))
    receipt = transaction.wait_for_confirmation(algod_client, txid, 4)
    asset_id = receipt.get("asset-index")
    if not asset_id:
        st.error("Asset creation failed")
        return None
    st.success(f"Asset {asset_id} created")
    listing = {
        "name": name,
        "description": description,
        "price": price,
        "asset_id": asset_id,
        "seller": addr,
        "image": base64.b64encode(image).decode(),
    }
    st.session_state["listings"].append(listing)
    st.session_state["last_listing"] = time.time()
    return asset_id


def send_payment(sender: str, receiver: str, amount: int) -> str | None:
    if algod_client is None:
        st.error("Algod client is not configured")
        return None
    params = algod_client.suggested_params()
    pay_txn = transaction.PaymentTxn(sender, params, receiver, amount)
    tx_json = json.dumps(transaction.transaction_to_dict(pay_txn))
    js = f"""
    const signPay = async () => {{
        if (!window.PeraWalletConnect) {{
            await import('https://cdn.jsdelivr.net/npm/@perawallet/connect@latest/dist/perawallet-connect.min.js');
        }}
        const pera = new window.PeraWalletConnect();
        const {{ signedTx }} = await pera.signTransaction([{{ txn: {tx_json} }}]);
        return btoa(String.fromCharCode.apply(null, signedTx));
    }};
    return await signPay();
    """
    signed = st_javascript(js, key="pay")
    if not signed:
        st.error("Payment not signed")
        return None
    txid = algod_client.send_raw_transaction(base64.b64decode(signed))
    transaction.wait_for_confirmation(algod_client, txid, 4)
    return txid


def transfer_asset(asset_id: int, sender: str, receiver: str) -> str | None:
    if algod_client is None:
        st.error("Algod client not configured")
        return None
    params = algod_client.suggested_params()
    txn = transaction.AssetTransferTxn(sender, params, receiver, 1, asset_id)
    tx_json = json.dumps(transaction.transaction_to_dict(txn))
    js = f"""
    const signTrans = async () => {{
        if (!window.PeraWalletConnect) {{
            await import('https://cdn.jsdelivr.net/npm/@perawallet/connect@latest/dist/perawallet-connect.min.js');
        }}
        const pera = new window.PeraWalletConnect();
        const {{ signedTx }} = await pera.signTransaction([{{ txn: {tx_json} }}]);
        return btoa(String.fromCharCode.apply(null, signedTx));
    }};
    return await signTrans();
    """
    signed = st_javascript(js, key="asa_transfer")
    if not signed:
        st.error("Transfer not signed")
        return None
    txid = algod_client.send_raw_transaction(base64.b64decode(signed))
    transaction.wait_for_confirmation(algod_client, txid, 4)
    return txid


st.title("Fleamarket")

wallet_btn = st.button("Connect Wallet")
if wallet_btn:
    connect_wallet()
addr = st.session_state.get("wallet")

st.header("List an Item")
with st.form("list_form"):
    name = st.text_input("Name")
    desc = st.text_area("Description")
    price = st.number_input("Price (Algos)", min_value=0.0, step=0.01)
    uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
    submit = st.form_submit_button("Create Listing")
    if submit:
        if not addr:
            st.error("Connect wallet first")
        elif time.time() - st.session_state["last_listing"] < 30:
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
                    asset_id = mint_asa(name, desc, int(price * 1_000_000), img_data)
                    if asset_id:
                        st.success(f"Listing created with ASA ID {asset_id}")

st.header("Available Items")
for item in st.session_state["listings"]:
    st.subheader(item["name"])
    st.write(item["description"])
    st.write(f"Price: {item['price']/1_000_000} Algos")
    st.image(io.BytesIO(base64.b64decode(item["image"])))
    if addr and addr != item["seller"]:
        if st.button(f"Buy {item['name']}"):
            if not item.get("sold"):
                txid = send_payment(addr, item["seller"], item["price"])
                if txid:
                    transfer_asset(item["asset_id"], item["seller"], addr)
                    item["sold"] = True
                    st.success("Purchase complete")
            else:
                st.warning("Item already sold")
