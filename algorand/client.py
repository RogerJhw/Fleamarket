import os

try:
    from algosdk.v2client import algod
except Exception:  # pragma: no cover - optional dependency
    algod = None


def get_algod_client() -> algod.AlgodClient:
    """Create an Algod client using environment variables."""
    address = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
    token = os.getenv("ALGOD_TOKEN", "")
    headers = {"X-API-Key": token} if token else None
    return algod.AlgodClient(token, address, headers)
