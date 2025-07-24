"""Utilities for working with the Algorand TestNet."""

try:
    from algorand_client import algod_client
except Exception:  # pragma: no cover - optional dependency
    algod_client = None

try:
    from .transactions import send_payment
except Exception:  # pragma: no cover - optional dependency
    send_payment = None

try:
    from .asset import create_asset
except Exception:  # pragma: no cover - optional dependency
    create_asset = None

try:
    from .contracts import deploy_app, compile_teal
except Exception:  # pragma: no cover - optional dependency
    deploy_app = None
    compile_teal = None

try:
    from .auction import (
        approval_program as auction_approval_program,
        clear_program as auction_clear_program,
        deploy_auction_app,
    )
except Exception:  # pragma: no cover - optional dependency
    auction_approval_program = None
    auction_clear_program = None
    deploy_auction_app = None

__all__ = [
    "algod_client",
    "send_payment",
    "create_asset",
    "deploy_app",
    "compile_teal",
    "deploy_auction_app",
    "auction_approval_program",
    "auction_clear_program",
]
