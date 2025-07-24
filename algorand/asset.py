try:
    from algosdk import account
    from algosdk.future import transaction
except Exception:  # pragma: no cover - optional dependency
    account = None
    transaction = None

import streamlit as st
from algorand_client import algod_client


def create_asset(private_key: str, asset_name: str, unit_name: str, total: int, decimals: int = 0, url: str = "") -> str:
    """Create an Algorand Standard Asset and return the transaction ID."""
    if algod_client is None:
        st.error("Algod client is not configured")
        return ""
    client = algod_client
    sender = account.address_from_private_key(private_key)
    params = client.suggested_params()
    txn = transaction.AssetCreateTxn(
        sender=sender,
        sp=params,
        total=total,
        decimals=decimals,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=asset_name,
        manager=sender,
        reserve=sender,
        freeze=sender,
        clawback=sender,
        url=url,
    )
    signed = txn.sign(private_key)
    txid = client.send_transaction(signed)
    return txid
