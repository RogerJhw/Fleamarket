import base64

try:
    from algosdk import account, transaction
except Exception:  # pragma: no cover - optional dependency
    account = None
    transaction = None

import streamlit as st
from algorand_client import algod_client


def compile_teal(teal_source: str) -> bytes:
    """Compile TEAL source to bytecode using the Algod client."""
    if algod_client is None:
        st.error("Algod client is not configured")
        return b""
    client = algod_client
    compile_response = client.compile(teal_source)
    return base64.b64decode(compile_response["result"])


def deploy_app(private_key: str, approval_program: str, clear_program: str,
               global_schema: transaction.StateSchema | None = None,
               local_schema: transaction.StateSchema | None = None,
               app_args: list[bytes] | None = None) -> str:
    """Deploy a PyTeal application and return the transaction ID."""
    if algod_client is None:
        st.error("Algod client is not configured")
        return ""
    client = algod_client
    sender = account.address_from_private_key(private_key)
    params = client.suggested_params()
    if global_schema is None:
        global_schema = transaction.StateSchema(0, 0)
    if local_schema is None:
        local_schema = transaction.StateSchema(0, 0)
    txn = transaction.ApplicationCreateTxn(
        sender=sender,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC.real,
        approval_program=compile_teal(approval_program),
        clear_program=compile_teal(clear_program),
        global_schema=global_schema,
        local_schema=local_schema,
        app_args=app_args,
    )
    signed = txn.sign(private_key)
    txid = client.send_transaction(signed)
    return txid
