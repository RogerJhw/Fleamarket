# Fleamarket Algorand TestNet Environment

This repository provides basic utilities for interacting with the Algorand
TestNet using Python. It is intended as a starting point for developing a
tokenized auction platform and includes helpers for deploying smart contracts,
sending test transactions, and creating Algorand Standard Assets (tokens).

## Prerequisites

* Python 3.11+
* An Algorand TestNet account funded with test Algos. You can obtain them from
the [Algorand TestNet Faucet](https://bank.testnet.algorand.network).
* Access to an Algod API endpoint (for example `https://testnet-api.algonode.cloud`).

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and set the Algod connection
   parameters. A sample is provided in `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and update the values if necessary.

```
ALGOD_ADDRESS=https://testnet-api.algonode.cloud
ALGOD_TOKEN=
```

If you use a provider that requires an API token (e.g. PureStake), set
`ALGOD_TOKEN` accordingly. The default configuration connects to the public
Algonode TestNet endpoint which does not require a token.

## Usage

The `algorand` package exposes helper functions for common tasks:

### Sending a payment transaction

```python
from algorand import send_payment

PRIVATE_KEY = "your 64-character hex private key"
RECEIVER = "ALGORECEIVERADDRESS..."

# send 1 Algo (1_000_000 microalgos)
txid = send_payment(PRIVATE_KEY, RECEIVER, 1_000_000)
print(f"Payment transaction ID: {txid}")
```

### Creating an Algorand Standard Asset

```python
from algorand import create_asset

PRIVATE_KEY = "..."

txid = create_asset(PRIVATE_KEY, "AuctionToken", "AUCT", total=1000)
print(f"Asset creation TXID: {txid}")
```

### Deploying a simple smart contract

```python
from algorand import deploy_app, compile_teal

approval_teal = "int 1"  # always approve
clear_teal = "int 1"

PRIVATE_KEY = "..."

txid = deploy_app(PRIVATE_KEY, approval_teal, clear_teal)
print(f"Application creation TXID: {txid}")
```

### Deploying the auction contract

The `auction` module provides a ready-to-use PyTeal contract that manages a
simple ASA auction. The asset is transferred to the application's address and
participants bid by sending a payment alongside the application call. The
highest bidder can claim the asset after the auction ends.

```python
from algorand import deploy_auction_app

PRIVATE_KEY = "seller private key"
ASA_ID = 123456  # ID of the asset to auction
START = 1700000000  # auction start timestamp
END = 1700003600    # auction end timestamp
RESERVE = 1_000_000  # minimum bid in microalgos

txid = deploy_auction_app(PRIVATE_KEY, ASA_ID, START, END, RESERVE)
print(f"Auction app creation TXID: {txid}")
```

## Testing

You can run a simple syntax check on the modules:

```bash
python -m py_compile algorand/*.py
```

These utilities interact with the Algorand TestNet. Ensure the environment
variables are set correctly before running the examples.
