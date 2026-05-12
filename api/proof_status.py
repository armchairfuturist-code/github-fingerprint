"""
Simple proof status store for tracking async proof generation.

Provides an in-memory dict-based store with thread-safe access via a lock.
Designed to be imported by both proof_tasks (writing status) and main.py
(reading status). A Redis or DB-backed store can be swapped in later for
production without changing the interface.

Proof status lifecycle:
    pending -> proof_generating -> proof_generated -> on_chain
                                 -> failed

Usage::

    store = ProofStatusStore()
    store.set_status("proof_abc123", "proof_generating")
    status = store.get_status("proof_abc123")
    # => {"proof_id": "proof_abc123", "status": "proof_generating", ...}
"""
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ProofStatusStore:
    """Thread-safe in-memory proof status store.

    Uses a dict backed by a ``threading.Lock``. The store maintains a flat
    dict of proof records keyed by ``proof_id``.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(
        self,
        proof_id: str,
        status: str,
        *,
        username: Optional[str] = None,
        proof_path: Optional[str] = None,
        tx_hash: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Set or update the status of a proof.

        Args:
            proof_id: The proof identifier.
            status: One of ``pending``, ``proof_generating``,
                ``proof_generated``, ``on_chain``, ``failed``.
            username: GitHub username (set on first creation).
            proof_path: Path to the generated proof file (optional).
            tx_hash: On-chain transaction hash (optional).
            error: Error message if failed (optional).
            metadata: Additional metadata to store (optional).

        Returns:
            The stored proof record.
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            record = self._store.get(proof_id, {})
            record["proof_id"] = proof_id
            record["status"] = status

            if username is not None:
                record["username"] = username

            if "created_at" not in record:
                record["created_at"] = now

            record["updated_at"] = now

            if proof_path is not None:
                record["proof_path"] = proof_path

            if tx_hash is not None:
                record["tx_hash"] = tx_hash

            if error is not None:
                record["error"] = error

            if metadata is not None:
                record["metadata"] = metadata

            self._store[proof_id] = record

        logger.info(
            "proof_store: proof_id=%s status=%s",
            proof_id,
            status,
        )
        return record

    def get_status(self, proof_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a proof.

        Args:
            proof_id: The proof identifier.

        Returns:
            The proof record dict, or ``None`` if not found.
        """
        with self._lock:
            return self._store.get(proof_id)

    def get_status_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get the latest proof status for a username.

        Args:
            username: GitHub username.

        Returns:
            The most recent proof record, or ``None`` if not found.
        """
        with self._lock:
            matches = [
                r for r in self._store.values()
                if r.get("username") == username
            ]
            if not matches:
                return None
            # Return the most recently updated record
            return max(matches, key=lambda r: r.get("updated_at", ""))

    def list_statuses(
        self,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        """List proof statuses, most recent first.

        Args:
            limit: Maximum number of records to return.
            status_filter: Optional status to filter by.

        Returns:
            List of proof record dicts.
        """
        with self._lock:
            records = list(self._store.values())
            if status_filter:
                records = [r for r in records if r.get("status") == status_filter]
            records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
            if limit is not None:
                records = records[:limit]
            return records

    def count_by_status(self) -> Dict[str, int]:
        """Count proofs by status — useful for queue depth gauges.

        Returns:
            Dict mapping status -> count.
        """
        with self._lock:
            counts: Dict[str, int] = {}
            for record in self._store.values():
                s = record.get("status", "unknown")
                counts[s] = counts.get(s, 0) + 1
            return counts

    def clear(self) -> int:
        """Clear all stored proof records (for testing).

        Returns:
            Number of records cleared.
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
        return count


# Module-level singleton — imported by proof_tasks and main.py
_store: ProofStatusStore = ProofStatusStore()


def get_store() -> ProofStatusStore:
    """Return the application-wide proof status store singleton."""
    return _store


def reset_store() -> None:
    """Reset the global store (for testing)."""
    global _store
    _store = ProofStatusStore()
