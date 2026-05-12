"""
End-to-end smoke test for the ZK proving flow.

Exercises the full proving lifecycle through the FastAPI TestClient with
mocked external dependencies. Tests that:

  - POST /score returns Ed25519 attestation immediately
  - Proof status transitions correctly through its lifecycle
  - Ed25519 attestation is returned even when Celery/Redis is unavailable
  - Proof status correctly shows 'failed' when the prover network is down
  - GET /proof/{username}/status returns correct status
  - The full attestation round-trip works end-to-end

These tests do NOT require a running Celery worker, Redis, a prover CLI
binary, or a Base Sepolia node. All external dependencies are mocked.
"""
import json
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper: minimal activity data
# ---------------------------------------------------------------------------

MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}


# ---------------------------------------------------------------------------
# Smoke test: /score returns Ed25519 attestation immediately
# ---------------------------------------------------------------------------

class TestScoreReturnsAttestation:
    """POST /score should return Ed25519 attestation regardless of ZK proof status."""

    def test_score_returns_attestation_immediately(self, monkeypatch):
        """POST /score should return Ed25519 attestation before proof is generated."""
        from api.main import app

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        response = client.post("/score", json={"username": "smoketest"})

        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None, "Ed25519 attestation should be returned immediately"
        assert "signature" in data["attestation"]
        assert "public_key" in data["attestation"]
        assert "signed_payload" in data["attestation"]
        assert data["proof_id"] is not None, "proof_id should be present in response"

    def test_attestation_is_verifiable(self, monkeypatch):
        """The attestation from /score should be verifiable via /verify."""
        from api.main import app

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "verify_smoke"})
        assert score_resp.status_code == 200
        att = score_resp.json()["attestation"]

        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })
        assert verify_resp.status_code == 200
        assert verify_resp.json()["valid"] is True
        assert verify_resp.json()["payload"]["username"] == "verify_smoke"


# ---------------------------------------------------------------------------
# Smoke test: Ed25519 fallback — score works when Celery/Redis is down
# ---------------------------------------------------------------------------

class TestEd25519Fallback:
    """Ed25519 attestation should be returned even when Celery/Redis is unavailable.

    The Celery enqueue call is wrapped in a try/except in the /score endpoint.
    If enqueue_proof raises an exception (e.g. Redis connection refused), the
    score response must still include Ed25519 attestation.
    """

    def test_score_succeeds_when_enqueue_fails(self, monkeypatch):
        """POST /score should succeed even when enqueue_proof raises."""
        from api.main import app

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        # Simulate Celery/Redis being down — enqueue_proof raises
        def failing_enqueue(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        monkeypatch.setattr("api.main.enqueue_proof", failing_enqueue)

        client = TestClient(app)
        response = client.post("/score", json={"username": "fallback_test"})

        # Should still return 200 with attestation
        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None, (
            "Ed25519 attestation must be returned even when Celery/Redis is down"
        )
        assert data["proof_id"] is not None, "proof_id should still be present"
        assert data["overall_score"] is not None, "score should be computed normally"

    def test_attestation_verifiable_during_fallback(self, monkeypatch):
        """Attestation during Celery fallback should still be verifiable."""
        from api.main import app

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        def failing_enqueue(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        monkeypatch.setattr("api.main.enqueue_proof", failing_enqueue)

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "fallback_verify"})
        assert score_resp.status_code == 200
        att = score_resp.json()["attestation"]

        # Verify the attestation
        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })
        assert verify_resp.status_code == 200
        assert verify_resp.json()["valid"] is True

    def test_proof_enqueue_failure_logged_does_not_block(self, monkeypatch):
        """enqueue_proof failure should not propagate to the caller."""
        from api.main import app

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        # Any exception type should be caught
        def failing_enqueue(*args, **kwargs):
            raise RuntimeError("Unexpected error in Celery enqueue")

        monkeypatch.setattr("api.main.enqueue_proof", failing_enqueue)

        client = TestClient(app)
        response = client.post("/score", json={"username": "exception_fallback"})
        assert response.status_code == 200
        assert response.json()["attestation"] is not None

    def test_proof_status_remains_unknown_when_enqueue_never_called(self, monkeypatch):
        """When Celery is down, proof status should not be set (stays unknown)."""
        from api.main import app
        from api.proof_status import reset_store, get_store

        reset_store()
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        # enqueue_proof is never called — simulate Celery down
        def failing_enqueue(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        monkeypatch.setattr("api.main.enqueue_proof", failing_enqueue)

        client = TestClient(app)
        response = client.post("/score", json={"username": "nocelery_user"})
        assert response.status_code == 200

        # Proof status should be unknown since enqueue never set it
        status_resp = client.get("/proof/nocelery_user/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "unknown"


# ---------------------------------------------------------------------------
# Smoke test: proof status lifecycle transitions
# ---------------------------------------------------------------------------

class TestProofStatusLifecycle:
    """Proof status should correctly transition through its lifecycle."""

    def test_proof_status_flow(self, monkeypatch):
        """Full lifecycle: pending → proof_generating → proof_generated → on_chain → failed."""
        from api.main import app
        from api.proof_status import reset_store, get_store

        reset_store()
        store = get_store()

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)

        # 1. POST /score — creates the entry
        score_resp = client.post("/score", json={"username": "lifecycle_user"})
        assert score_resp.status_code == 200
        proof_id = score_resp.json().get("proof_id")
        assert proof_id is not None

        # Manually drive status transitions (in production, Celery drives these)
        store.set_status(proof_id, "pending", username="lifecycle_user")

        r = client.get("/proof/lifecycle_user/status")
        assert r.json()["status"] == "pending", f"Expected pending, got {r.json()['status']}"

        # 2. proof_generating
        store.set_status(proof_id, "proof_generating")
        r = client.get("/proof/lifecycle_user/status")
        assert r.json()["status"] == "proof_generating"

        # 3. proof_generated
        store.set_status(proof_id, "proof_generated", proof_path="/tmp/proof.bin")
        r = client.get("/proof/lifecycle_user/status")
        assert r.json()["status"] == "proof_generated"
        assert r.json()["proof_path"] == "/tmp/proof.bin"

        # 4. on_chain
        store.set_status(proof_id, "on_chain", tx_hash="0xdeadbeef")
        r = client.get("/proof/lifecycle_user/status")
        assert r.json()["status"] == "on_chain"
        assert r.json()["tx_hash"] == "0xdeadbeef"

        # 5. failed
        store.set_status(proof_id, "failed", error="Prover network timeout")
        r = client.get("/proof/lifecycle_user/status")
        assert r.json()["status"] == "failed"
        assert r.json()["error"] == "Prover network timeout"

    def test_proof_status_includes_attestation(self, monkeypatch):
        """Each status response should include Ed25519 attestation."""
        from api.main import app
        from api.proof_status import reset_store, get_store

        reset_store()
        store = get_store()

        client = TestClient(app)
        store.set_status("proof_att", "proof_generated", username="att_user")
        r = client.get("/proof/att_user/status")
        assert r.status_code == 200
        data = r.json()
        assert "attestation" in data
        att = data["attestation"]
        # Attestation may be None if signing key not initialized,
        # but the key should be present
        if att is not None:
            assert "signature" in att
            assert "public_key" in att

    def test_unknown_user_returns_unknown_status(self):
        """Non-existent user should return status 'unknown'."""
        from api.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        r = client.get("/proof/does_not_exist/status")
        assert r.status_code == 200
        assert r.json()["status"] == "unknown"


# ---------------------------------------------------------------------------
# Smoke test: Celery task failure modes
# ---------------------------------------------------------------------------

class TestCeleryTaskFailureModes:
    """Proof tasks should handle failure modes gracefully without crashing."""

    MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}

    def test_prover_cli_missing_is_handled(self):
        """Missing prover CLI binary should raise FileNotFoundError (test catches it)."""
        from api.prover_client import run_proof

        with patch.dict("os.environ", {"SCORING_PROVER_CLI": "/nonexistent/binary"}):
            with pytest.raises(FileNotFoundError):
                run_proof("missing_cli", self.MINIMAL_ACTIVITY)

    def test_retry_on_network_error(self):
        """Task should raise on exception so Celery retries."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.side_effect = ConnectionError("Prover network timeout")

            with pytest.raises(ConnectionError):
                generate_proof.run("network_fail", self.MINIMAL_ACTIVITY, "proof_fail_01")

            mock_store.set_status.assert_any_call(
                "proof_fail_01", "failed",
                error="ConnectionError: Prover network timeout",
            )

    def test_failed_proof_sets_failed_status(self):
        """CLI failure should set 'failed' status in store."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.return_value = {
                "status": "proof_failed",
                "error": "Invalid SP1 proof: constraint mismatch",
            }

            generate_proof.run("invalid_input", self.MINIMAL_ACTIVITY, "proof_invalid_01")

            mock_store.set_status.assert_any_call(
                "proof_invalid_01", "failed",
                error="Invalid SP1 proof: constraint mismatch",
                metadata={"status": "proof_failed", "error": "Invalid SP1 proof: constraint mismatch"},
            )

    def test_generate_proof_retry_config(self):
        """Task should have correct retry configuration for transient failures."""
        from api.proof_tasks import generate_proof
        assert generate_proof.max_retries == 3
        assert generate_proof.retry_backoff is True
        assert generate_proof.retry_backoff_max == 600
        assert generate_proof.retry_jitter is True


# ---------------------------------------------------------------------------
# Smoke test: /proof endpoint with multiple users
# ---------------------------------------------------------------------------

class TestMultipleUsers:
    """Proof status should be correctly scoped per user."""

    def test_multiple_users_have_independent_status(self):
        """Multiple users should have independent proof statuses."""
        from api.main import app
        from api.proof_status import reset_store, get_store
        from fastapi.testclient import TestClient

        reset_store()
        store = get_store()
        store.set_status("p1", "proof_generated", username="alice")
        store.set_status("p2", "pending", username="bob")
        store.set_status("p3", "failed", username="charlie")

        client = TestClient(app)

        assert client.get("/proof/alice/status").json()["status"] == "proof_generated"
        assert client.get("/proof/bob/status").json()["status"] == "pending"
        assert client.get("/proof/charlie/status").json()["status"] == "failed"
        assert client.get("/proof/dave/status").json()["status"] == "unknown"


# ---------------------------------------------------------------------------
# Smoke test: full round-trip (score → attest → verify → proof status)
# ---------------------------------------------------------------------------

class TestFullRoundTrip:
    """Full end-to-end attestation round-trip with mocked proving."""

    def test_full_round_trip(self, monkeypatch):
        """Score → attest → verify → proof status."""
        from api.main import app
        from api.proof_status import reset_store, get_store
        from fastapi.testclient import TestClient

        reset_store()
        store = get_store()

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)

        # 1. Score
        score_resp = client.post("/score", json={"username": "roundtrip_user"})
        assert score_resp.status_code == 200
        data = score_resp.json()
        assert data["attestation"] is not None
        proof_id = data["proof_id"]

        # 2. Verify attestation
        att = data["attestation"]
        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })
        assert verify_resp.status_code == 200
        assert verify_resp.json()["valid"] is True
        assert verify_resp.json()["payload"]["username"] == "roundtrip_user"

        # 3. Set proof to proof_generated to simulate completion
        store.set_status(proof_id, "proof_generated", proof_path="/tmp/proof.bin",
                         username="roundtrip_user",
                         metadata={"proving_time_ms": 5000, "prover": "local"})

        # 4. Check proof status
        status_resp = client.get("/proof/roundtrip_user/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["proof_id"] == proof_id
        assert status_data["status"] == "proof_generated"
        assert status_data["proof_path"] == "/tmp/proof.bin"

    def test_full_round_trip_with_failure(self, monkeypatch):
        """Score → failed proof → status shows failed with error."""
        from api.main import app
        from api.proof_status import reset_store, get_store
        from fastapi.testclient import TestClient

        reset_store()
        store = get_store()

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)

        # 1. Score
        score_resp = client.post("/score", json={"username": "failure_roundtrip"})
        assert score_resp.status_code == 200
        proof_id = score_resp.json()["proof_id"]

        # 2. Set proof to failed
        store.set_status(proof_id, "failed", username="failure_roundtrip",
                         error="SP1 prover constraint system check failed")

        # 3. Check failed status
        status_resp = client.get("/proof/failure_roundtrip/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "failed"
        assert "SP1 prover" in status_data["error"]


# ---------------------------------------------------------------------------
# Smoke test: queue depth gauge (ProofStatusStore.count_by_status)
# ---------------------------------------------------------------------------

class TestQueueDepthGauge:
    """ProofStatusStore.count_by_status provides queue depth visibility."""

    def test_count_by_status_reflects_store_state(self):
        """count_by_status should correctly count proofs by status."""
        from api.proof_status import ProofStatusStore

        store = ProofStatusStore()
        store.set_status("p1", "pending", username="u1")
        store.set_status("p2", "proof_generating", username="u2")
        store.set_status("p3", "pending", username="u3")
        store.set_status("p4", "proof_generated", username="u4")
        store.set_status("p5", "failed", username="u5")
        store.set_status("p6", "proof_generating", username="u6")

        counts = store.count_by_status()
        assert counts.get("pending") == 2
        assert counts.get("proof_generating") == 2
        assert counts.get("proof_generated") == 1
        assert counts.get("failed") == 1
        assert counts.get("on_chain") is None

    def test_empty_store_returns_empty_counts(self):
        """Empty store should return empty (or missing) counts."""
        from api.proof_status import ProofStatusStore

        store = ProofStatusStore()
        counts = store.count_by_status()
        assert isinstance(counts, dict)
        assert len(counts) == 0


# ---------------------------------------------------------------------------
# Smoke test: Ed25519 attestation returned even when prover network is down
# ---------------------------------------------------------------------------

class TestProverNetworkDown:
    """Score should work when prover network is unreachable."""

    def test_score_succeeds_when_prover_network_down(self, monkeypatch):
        """POST /score should succeed when the SP1 prover network is unreachable
        (simulated by enqueue_proof raising connection error)."""
        from api.main import app
        from fastapi.testclient import TestClient

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: (
            (_ for _ in ()).throw(ConnectionError("Prover network unreachable"))
        ))

        client = TestClient(app)
        response = client.post("/score", json={"username": "prover_down"})
        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None
        assert data["overall_score"] is not None

    def test_proof_status_shows_unknown_when_prover_down(self, monkeypatch):
        """Proof status should be 'unknown' when prover is unreachable
        (enqueue never set a status)."""
        from api.main import app
        from api.proof_status import reset_store
        from fastapi.testclient import TestClient

        reset_store()
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        def failing_enqueue(*args, **kwargs):
            raise ConnectionError("Prover network unreachable")

        monkeypatch.setattr("api.main.enqueue_proof", failing_enqueue)

        client = TestClient(app)
        client.post("/score", json={"username": "prover_down_status"})
        status_resp = client.get("/proof/prover_down_status/status")
        assert status_resp.json()["status"] == "unknown"


# ---------------------------------------------------------------------------
# Smoke test: invalid GITHUB_TOKEN failure mode
# ---------------------------------------------------------------------------

class TestInvalidGitHubToken:
    """API should return proper error when GITHUB_TOKEN is invalid."""

    def test_invalid_token_returns_value_error(self, monkeypatch):
        """Missing GITHUB_TOKEN should raise ValueError on first use."""
        from api.main import _get_github_client
        import api.main as main

        # Force re-initialization by clearing the cached client
        main._github_client_instance = None
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            _get_github_client()

    def test_score_endpoint_without_token_returns_400(self, monkeypatch):
        """POST /score without GITHUB_TOKEN should return 400 (ValueError → Bad Request)."""
        from api.main import app
        from fastapi.testclient import TestClient

        # Clear the cached client and remove GITHUB_TOKEN
        import api.main as main
        main._github_client_instance = None
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        # Don't mock _get_github_client — let it fail
        client = TestClient(app)
        response = client.post("/score", json={"username": "tokenless_user"})
        assert response.status_code == 400
        assert "GITHUB_TOKEN" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Script entry point (for direct execution as a smoke test)
# ---------------------------------------------------------------------------

def run_smoke_test():
    """Run the E2E smoke test as a standalone script.

    This can be invoked directly::

        python -m tests.test_proving_e2e

    or via pytest::

        pytest tests/test_proving_e2e.py -v

    The script entry point provides a quick pass/fail for CI pipelines.
    """
    import sys

    class QuietReporter:
        """Minimal output for smoke test."""

        def __init__(self):
            self.passed = 0
            self.failed = 0

        def pytest_runtest_logreport(self, report):
            if report.when == "call":
                if report.passed:
                    self.passed += 1
                else:
                    self.failed += 1
                    print(f"FAIL: {report.nodeid}")

        def pytest_sessionfinish(self):
            print(f"\nSmoke test: {self.passed} passed, {self.failed} failed")
            return self.failed == 0

    reporter = QuietReporter()
    exit_code = pytest.main(
        [__file__, "-v", "--tb=short", "-q"],
        plugins=[reporter],
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    run_smoke_test()
