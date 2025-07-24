import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
try:
    from algosdk.v2client.algod import AlgodClient
except Exception:  # pragma: no cover - optional dependency
    AlgodClient = None

# Load environment variables from .env if present
load_dotenv(Path(__file__).resolve().with_name('.env'))

ALGOD_ENDPOINT = os.getenv('ALGOD_ENDPOINT', 'https://testnet-api.algonode.cloud')
ALGOD_TOKEN = os.getenv('ALGOD_TOKEN', '')


def _init_client() -> Optional['AlgodClient']:
    if AlgodClient is None:
        return None
    try:
        headers = {'X-API-Key': ALGOD_TOKEN} if ALGOD_TOKEN else None
        return AlgodClient(ALGOD_TOKEN, ALGOD_ENDPOINT, headers)
    except Exception:
        return None


algod_client = _init_client()
