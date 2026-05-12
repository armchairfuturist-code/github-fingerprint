"""
Tests for the Celery proof generation tasks.

Tests that the task correctly delegates to run_proof(), updates the
proof status store through its lifecycle, and handles retries.
"""
from unittest.mock import MagicMock, patch
import pytest


class TestEnqueueProof:
    """Tests for the enqueue_proof helper function."""

    def test_enqueue_creates_pending_status(self):
        """enqueue_proof should set status to pending before enqueuing."""
        with (
            patch("api.proof_tasks.generate_proof.delay") as mock_delay,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_delay.return_value = MagicMock(id="celery-task-123")

            from api.proof_tasks import enqueue_proof
            task_id = enqueue_proof("testuser", {"repos": []}, "proof_abc")

            # Verify status was set to pending
            mock_store.set_status.assert_called_once_with(
                "proof_abc", "pending", username="testuser",
            )
            # Verify delay was called with correct args
            mock_delay.assert_called_once_with(
                "testuser", {"repos": []}, "proof_abc",
            )
            assert task_id == "celery-task-123"

    def test_enqueue_returns_task_id(self):
        """enqueue_proof should return the Celery task ID."""
        with (
            patch("api.proof_tasks.generate_proof.delay") as mock_delay,
            patch("api.proof_tasks.get_store"),
        ):
            mock_delay.return_value = MagicMock(id="task-uuid-456")
            from api.proof_tasks import enqueue_proof
            task_id = enqueue_proof("u", {}, "p1")
            assert task_id == "task-uuid-456"


class TestGenerateProofTask:
    """Tests for the generate_proof Celery task."""

    MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}

    def test_task_transitions_to_generating(self):
        """Task should set status to proof_generating on first attempt."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.return_value = {
                "status": "proof_generated",
                "proof_path": "/tmp/proof.bin",
                "proving_time_ms": 5000,
                "proving_time_seconds": 5.0,
                "prover": "local",
                "input_summary": {"repos": 0, "commits": 0},
            }

            # Simulate task execution via eager mode
            result = generate_proof.run(
                "testuser", self.MINIMAL_ACTIVITY, "proof_abc",
            )

            # Should have set proof_generating first
            mock_store.set_status.assert_any_call(
                "proof_abc", "proof_generating", username="testuser",
            )
            assert result["status"] == "proof_generated"

    def test_task_updates_status_on_success(self):
        """Successful proof should set status to proof_generated."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.return_value = {
                "status": "proof_generated",
                "proof_path": "/tmp/proof.bin",
                "proving_time_ms": 5000,
                "proving_time_seconds": 5.0,
                "prover": "local",
                "input_summary": {"repos": 0, "commits": 0},
            }

            generate_proof.run("testuser", self.MINIMAL_ACTIVITY, "proof_abc")

            # Verify final status update
            mock_store.set_status.assert_any_call(
                "proof_abc",
                "proof_generated",
                proof_path="/tmp/proof.bin",
                metadata={
                    "proving_time_ms": 5000,
                    "proving_time_seconds": 5.0,
                    "prover": "local",
                    "input_summary": {"repos": 0, "commits": 0},
                },
            )

    def test_task_handles_cli_failure(self):
        """CLI failure should set status to failed."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.return_value = {
                "status": "proof_failed",
                "error": "Invalid proof data",
            }

            generate_proof.run("testuser", self.MINIMAL_ACTIVITY, "proof_abc")

            # Verify failed status
            mock_store.set_status.assert_any_call(
                "proof_abc", "failed",
                error="Invalid proof data",
                metadata={"status": "proof_failed", "error": "Invalid proof data"},
            )

    def test_task_retries_on_exception(self):
        """Task should raise on exception so Celery retries."""
        from api.proof_tasks import generate_proof

        with (
            patch("api.proof_tasks.run_proof") as mock_run,
            patch("api.proof_tasks.get_store") as mock_get_store,
        ):
            mock_store = MagicMock()
            mock_get_store.return_value = mock_store
            mock_run.side_effect = ConnectionError("Network timeout")

            with pytest.raises(ConnectionError):
                generate_proof.run(
                    "testuser", self.MINIMAL_ACTIVITY, "proof_abc",
                )

            # Should have set failed status before re-raising
            mock_store.set_status.assert_any_call(
                "proof_abc", "failed",
                error="ConnectionError: Network timeout",
            )

    def test_task_name_and_queue(self):
        """Task should have correct name and queue."""
        from api.proof_tasks import generate_proof
        assert generate_proof.name == "generate_proof"
        assert generate_proof.queue == "proof_generation"

    def test_task_retry_config(self):
        """Task should have correct retry configuration."""
        from api.proof_tasks import generate_proof
        # The base class provides these
        assert generate_proof.max_retries == 3
        assert generate_proof.retry_backoff is True
        assert generate_proof.retry_backoff_max == 600
        assert generate_proof.retry_jitter is True


class TestProofTaskBase:
    """Tests for the ProofTaskBase task class."""

    def test_base_has_correct_retries(self):
        """ProofTaskBase should have 3 max retries with exponential backoff."""
        from api.proof_tasks import ProofTaskBase
        assert ProofTaskBase.max_retries == 3
        assert ProofTaskBase.retry_backoff is True
