import base64
from algosdk import account, transaction

from .client import get_algod_client


def compile_teal(teal_source: str) -> bytes:
    """Compile TEAL source to bytecode using the Algod client."""
    client = get_algod_client()
    compile_response = client.compile(teal_source)
    return base64.b64decode(compile_response["result"])


def deploy_app(private_key: str, approval_program: str, clear_program: str,
               global_schema: transaction.StateSchema | None = None,
               local_schema: transaction.StateSchema | None = None,
               app_args: list[bytes] | None = None) -> str:
    """Deploy a PyTeal application and return the transaction ID."""
    client = get_algod_client()
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
