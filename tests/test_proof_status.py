"""
Tests for the proof status store.
"""
import pytest
from api.proof_status import ProofStatusStore, get_store, reset_store


class TestProofStatusStore:
    """Unit tests for the in-memory ProofStatusStore."""

    def setup_method(self):
        self.store = ProofStatusStore()

    def test_set_and_get_status(self):
        """Setting status should store record and retrieving should return it."""
        self.store.set_status("proof_abc", "pending", username="testuser")
        record = self.store.get_status("proof_abc")
        assert record is not None
        assert record["proof_id"] == "proof_abc"
        assert record["status"] == "pending"
        assert record["username"] == "testuser"
        assert "created_at" in record
        assert "updated_at" in record

    def test_update_status(self):
        """Updating status should keep created_at but update updated_at."""
        self.store.set_status("proof_abc", "pending", username="testuser")
        original = self.store.get_status("proof_abc")
        self.store.set_status("proof_abc", "proof_generating")
        updated = self.store.get_status("proof_abc")
        assert updated["created_at"] == original["created_at"]
        assert updated["status"] == "proof_generating"
        assert updated["status"] == "proof_generating"

    def test_get_nonexistent_returns_none(self):
        """Getting status for unknown proof_id should return None."""
        record = self.store.get_status("nonexistent")
        assert record is None

    def test_status_lifecycle(self):
        """Full status lifecycle should work end-to-end."""
        store = self.store
        store.set_status("proof_123", "pending", username="alice")
        assert store.get_status("proof_123")["status"] == "pending"
        store.set_status("proof_123", "proof_generating")
        assert store.get_status("proof_123")["status"] == "proof_generating"
        store.set_status("proof_123", "proof_generated", proof_path="/tmp/proof.bin")
        assert store.get_status("proof_123")["status"] == "proof_generated"
        assert store.get_status("proof_123")["proof_path"] == "/tmp/proof.bin"
        store.set_status("proof_123", "on_chain", tx_hash="0xabc123")
        assert store.get_status("proof_123")["status"] == "on_chain"
        assert store.get_status("proof_123")["tx_hash"] == "0xabc123"

    def test_failed_status_with_error(self):
        """Failed status should store the error message."""
        self.store.set_status("proof_err", "failed", error="CLI crashed")
        record = self.store.get_status("proof_err")
        assert record["status"] == "failed"
        assert record["error"] == "CLI crashed"

    def test_set_status_with_metadata(self):
        """Should store additional metadata dict."""
        self.store.set_status("proof_meta", "proof_generated", metadata={
            "proving_time_ms": 5000,
            "prover": "local",
        })
        record = self.store.get_status("proof_meta")
        assert record["metadata"]["proving_time_ms"] == 5000
        assert record["metadata"]["prover"] == "local"

    def test_get_status_by_username(self):
        """Should find the latest proof by username."""
        self.store.set_status("proof_a", "proof_generated", username="alice")
        self.store.set_status("proof_b", "pending", username="bob")
        self.store.set_status("proof_c", "failed", username="alice")
        alice_latest = self.store.get_status_by_username("alice")
        assert alice_latest is not None
        assert alice_latest["proof_id"] == "proof_c"
        bob_status = self.store.get_status_by_username("bob")
        assert bob_status["proof_id"] == "proof_b"
        charlie_status = self.store.get_status_by_username("charlie")
        assert charlie_status is None

    def test_list_statuses(self):
        """Should list all statuses."""
        self.store.set_status("proof_a", "pending", username="alice")
        self.store.set_status("proof_b", "proof_generated", username="bob")
        self.store.set_status("proof_c", "failed", username="charlie")
        all_records = self.store.list_statuses()
        assert len(all_records) == 3
        # All proof_ids should be present
        ids = {r["proof_id"] for r in all_records}
        assert ids == {"proof_a", "proof_b", "proof_c"}

    def test_list_statuses_with_filter(self):
        """Should filter by status."""
        self.store.set_status("proof_a", "pending", username="alice")
        self.store.set_status("proof_b", "proof_generated", username="bob")
        self.store.set_status("proof_c", "failed", username="charlie")
        filtered = self.store.list_statuses(status_filter="pending")
        assert len(filtered) == 1
        assert filtered[0]["proof_id"] == "proof_a"

    def test_list_statuses_limit(self):
        """Should respect the limit parameter."""
        for i in range(10):
            self.store.set_status(f"proof_{i}", "pending", username=f"user_{i}")
        limited = self.store.list_statuses(limit=3)
        assert len(limited) == 3
        unlimited = self.store.list_statuses(limit=None)
        assert len(unlimited) == 10

    def test_count_by_status(self):
        """Should correctly count records by status."""
        self.store.set_status("p1", "pending", username="u1")
        self.store.set_status("p2", "proof_generating", username="u2")
        self.store.set_status("p3", "pending", username="u3")
        self.store.set_status("p4", "failed", username="u4")
        counts = self.store.count_by_status()
        assert counts.get("pending") == 2
        assert counts.get("proof_generating") == 1
        assert counts.get("failed") == 1

    def test_clear(self):
        """Clearing should remove all records and return count."""
        self.store.set_status("p1", "pending", username="u1")
        self.store.set_status("p2", "pending", username="u2")
        count = self.store.clear()
        assert count == 2
        assert self.store.list_statuses() == []

    def test_thread_safety(self):
        """Concurrent writes should not corrupt state."""
        import threading
        n_threads = 10
        n_writes = 100

        def writer(thread_id):
            for i in range(n_writes):
                self.store.set_status(
                    f"t{thread_id}_p{i}",
                    "pending",
                    username=f"user_{thread_id}",
                )

        threads = [
            threading.Thread(target=writer, args=(tid,))
            for tid in range(n_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        all_records = self.store.list_statuses(limit=None)
        assert len(all_records) == n_threads * n_writes


class TestProofStatusStoreSingleton:
    """Tests for the module-level singleton accessor."""

    def test_get_store_returns_singleton(self):
        """get_store should always return the same instance."""
        store_a = get_store()
        store_b = get_store()
        assert store_a is store_b

    def test_reset_store_creates_new_instance(self):
        """reset_store should create a fresh singleton."""
        store_a = get_store()
        store_a.set_status("test", "pending", username="u")
        reset_store()
        store_b = get_store()
        assert store_a is not store_b
        assert store_b.get_status("test") is None
