"""
Wallet Store — Local JSON-backed mapping of GitHub usernames to wallet data.

Thread-safe singleton pattern (same as ProofStatusStore in api/proof_status.py).
Persists to ``wallet_store.json`` in the project root.

Data shape per user::

    {
        "wallet_id": "id2tptkqrxd39qo9j423etij",
        "address": "0xF1DBff66C993EE895C8cb176c30b07A559d76496",
        "chain_type": "ethereum",
        "created_at": "2026-05-12T10:00:00Z",
        "attestation_hashes": [
            "sha256:abc123...",
        ],
    }
"""
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STORE_FILENAME = "wallet_store.json"


class WalletStore:
    """Thread-safe, JSON-backed store mapping GitHub usernames to wallet data."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self._path = path or _default_store_path()
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Return the wallet record for *username*, or None."""
        with self._lock:
            return self._data.get(username.lower())

    def set_wallet(self, username: str, wallet_data: Dict[str, Any]) -> None:
        """Store or overwrite the wallet record for *username*."""
        with self._lock:
            self._data[username.lower()] = wallet_data
            self._save()

    def add_attestation_hash(
        self, username: str, attestation_hash: str
    ) -> None:
        """Append an attestation hash to the user's wallet backpack."""
        with self._lock:
            key = username.lower()
            if key not in self._data:
                self._data[key] = {
                    "wallet_id": None,
                    "address": None,
                    "chain_type": None,
                    "created_at": None,
                    "attestation_hashes": [],
                }
            hashes: List[str] = self._data[key].setdefault(
                "attestation_hashes", []
            )
            if attestation_hash not in hashes:
                hashes.append(attestation_hash)
            self._save()

    def all_usernames(self) -> List[str]:
        """Return all usernames that have wallet records."""
        with self._lock:
            return list(self._data.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load store from disk (silent if file missing or corrupt)."""
        if not os.path.isfile(self._path):
            logger.info("No existing wallet store at %s — starting fresh", self._path)
            self._data = {}
            return
        try:
            with open(self._path, "r") as f:
                self._data = json.load(f)
            logger.info("Loaded wallet store from %s (%d entries)", self._path, len(self._data))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load wallet store from %s: %s — starting fresh", self._path, exc)
            self._data = {}

    def _save(self) -> None:
        """Write store to disk atomically."""
        tmp = self._path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2, sort_keys=True)
            os.replace(tmp, self._path)
        except OSError as exc:
            logger.error("Failed to save wallet store: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_store_instance: Optional[WalletStore] = None
_store_lock = threading.Lock()


def _default_store_path() -> str:
    """Return the default store path relative to the project root."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), STORE_FILENAME)


def get_store(path: Optional[str] = None) -> WalletStore:
    """Return the module-level WalletStore singleton."""
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = WalletStore(path=path)
    return _store_instance
