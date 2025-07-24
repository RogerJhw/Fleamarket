try:
    from algosdk import account, transaction
except Exception:  # pragma: no cover - optional dependency
    account = None
    transaction = None

import streamlit as st
from algorand_client import algod_client


def send_payment(private_key: str, receiver: str, amount: int) -> str:
    """Send Algos to ``receiver`` and return the transaction ID."""
    if algod_client is None:
        st.error("Algod client is not configured")
        return ""
    client = algod_client
    sender = account.address_from_private_key(private_key)
    params = client.suggested_params()
    txn = transaction.PaymentTxn(sender, params, receiver, amount)
    signed = txn.sign(private_key)
    txid = client.send_transaction(signed)
    return txid
