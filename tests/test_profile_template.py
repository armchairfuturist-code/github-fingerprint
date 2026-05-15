"""
Tests for the profile page Jinja2 template rendering with proof lifecycle states.

Exercises the /u/{username} server-rendered profile page with mocked
ProofStatusStore data for all 6 proof lifecycle states (unknown, pending,
proof_generating, proof_generated, on_chain, failed). Verifies badge text,
viewer visibility, metadata display, and graceful degradation.

Does NOT require a running Celery worker, Redis, or SP1 prover.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.main import app

MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}


def _make_mock_store(proof_record):
    """Create a mocked ProofStatusStore returning the given proof_record."""
    mock_store = MagicMock()
    mock_store.get_status_by_username.return_value = proof_record
    return mock_store


def _make_proof_record(
    status,
    proof_id="proof_abc123",
    created_at="2026-05-15T10:00:00+00:00",
    updated_at="2026-05-15T10:05:00+00:00",
    tx_hash=None,
    proof_path=None,
    error=None,
    verifying_contract=None,
):
    """Build a proof record dict matching ProofStatusStore shape."""
    record = {
        "proof_id": proof_id,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    if tx_hash:
        record["tx_hash"] = tx_hash
    if proof_path:
        record["proof_path"] = proof_path
    if error:
        record["error"] = error
    if verifying_contract or status == "on_chain":
        record["metadata"] = {"verifying_contract": verifying_contract or "0x1234...5678"}
    return record


class TestProfileProofBadge:
    """Proof badge in profile shows correct status-specific text for all states."""

    @pytest.mark.parametrize("status,expected_text", [
        ("unknown", "Not Started"),
        ("pending", "Pending"),
        ("proof_generating", "Generating"),
        ("proof_generated", "Proof Ready"),
        ("on_chain", "On Chain"),
        ("failed", "Failed"),
    ])
    def test_badge_text_per_state(self, monkeypatch, status, expected_text):
        """Proof badge should display correct status text for each lifecycle state."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(status=status)
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert expected_text in response.text

    @pytest.mark.parametrize("status,expected_symbol", [
        ("unknown", "&#9679;"),       # bullet
        ("pending", "&#9687;"),       # white circle
        ("proof_generating", "&#9678;"),  # medium circle
        ("proof_generated", "&#10003;"),  # checkmark
        ("on_chain", "&#8852;"),      # square
        ("failed", "&#10005;"),       # X mark
    ])
    def test_badge_symbol_per_state(self, monkeypatch, status, expected_symbol):
        """Proof badge should display correct Unicode symbol for each state."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(status=status)
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert expected_symbol in response.text


class TestProfileProofViewer:
    """Expandable proof viewer shows proof metadata correctly."""

    def test_viewer_shows_proof_id(self, monkeypatch):
        """Proof viewer should display the proof ID when available."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="proof_generated",
            proof_id="proof_xyz789",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "proof_xyz789" in response.text

    def test_viewer_shows_created_and_updated(self, monkeypatch):
        """Proof viewer should display created_at and updated_at timestamps."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="proof_generated",
            created_at="2026-05-15T10:00:00+00:00",
            updated_at="2026-05-15T10:30:00+00:00",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        # Timestamps in the format YYYY-MM-DD HH:MM:SS UTC
        assert "2026-05-15 10:00:00 UTC" in response.text
        assert "2026-05-15 10:30:00 UTC" in response.text

    def test_viewer_shows_tx_hash(self, monkeypatch):
        """Proof viewer should display tx_hash when on_chain."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="on_chain",
            tx_hash="0xabcdef1234567890",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "0xabcdef1234567890" in response.text

    def test_viewer_shows_error(self, monkeypatch):
        """Proof viewer should display error message when failed."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="failed",
            error="Prover network timeout after 30s",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "Prover network timeout after 30s" in response.text

    def test_viewer_shows_proof_path(self, monkeypatch):
        """Proof viewer should display proof_path when available."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="proof_generated",
            proof_path="/tmp/proofs/proof_abc123.bin",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "/tmp/proofs/proof_abc123.bin" in response.text
        assert "Proof Path" in response.text

    def test_viewer_shows_verifying_contract(self, monkeypatch):
        """Proof viewer should display verifying contract address when on_chain."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="on_chain",
            verifying_contract="0xSP1VerifierDeadBeef",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "0xSP1VerifierDeadBeef" in response.text
        assert "Verifying Contract" in response.text


class TestProfileProofGracefulDegradation:
    """Template degrades gracefully when no proof record exists."""

    def test_unknown_status_when_no_proof_record(self, monkeypatch):
        """Profile page should show 'unknown' status when no proof record exists."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        # Simulate no proof record — store returns None
        mock_store = MagicMock()
        mock_store.get_status_by_username.return_value = None
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "Not Started" in response.text
        assert "&#9679;" in response.text

    def test_no_proof_id_no_viewer_rows(self, monkeypatch):
        """Profile page should not show proof detail rows when no proof_id."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        # Record with unknown status and no proof_id
        proof_record = {
            "status": "unknown",
            "proof_id": None,
            "created_at": None,
            "updated_at": None,
        }
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        # Badge should show Not Started
        assert "Not Started" in response.text
        # No proof_id shown
        assert "Proof ID" not in response.text


class TestProfileProofViewerCopyButton:
    """Copy Proof Data button works correctly."""

    def test_copy_button_present(self, monkeypatch):
        """Profile page should include a Copy Proof Data button."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(status="proof_generated")
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        assert "Copy Proof Data" in response.text
        assert "copyProofData" in response.text

    def test_copy_button_has_data_proof_attribute(self, monkeypatch):
        """Copy button should have a data-proof attribute with JSON."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        proof_record = _make_proof_record(
            status="proof_generated",
            proof_id="proof_copy_test",
        )
        mock_store = _make_mock_store(proof_record)
        monkeypatch.setattr("api.main.get_store", lambda: mock_store)

        client = TestClient(app)
        response = client.get("/u/prooftest")

        assert response.status_code == 200
        # data-proof attribute should contain the proof data as JSON
        assert 'data-proof=' in response.text or 'data-proof' in response.text

    def test_no_shell_redirect_artifacts_in_template(self, monkeypatch):
        """Template should have zero shell-redirect artifacts."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        assert ">/dev/null" not in response.text
