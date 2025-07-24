from algorand_client import algod_client


def get_algod_client():
    """Return the shared Algod client instance."""
    return algod_client
