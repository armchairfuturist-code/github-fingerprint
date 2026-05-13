"""
Wallet abstraction module — Privy-powered embedded wallets and data backpack.

Provides:
- ``create_wallet(username)`` — Create a Privy wallet for a GitHub user.
- ``get_wallet(wallet_id)`` — Look up wallet details by Privy ID.
- ``get_store()`` — Module-level WalletStore singleton.
- ``is_available()`` — Whether Privy credentials are configured.
"""
from wallet.provider import create_wallet, get_wallet, is_available
from wallet.store import WalletStore, get_store

__all__ = [
    "create_wallet",
    "get_wallet",
    "get_store",
    "WalletStore",
    "is_available",
]
