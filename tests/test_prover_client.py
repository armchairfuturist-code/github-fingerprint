"""
Unit tests for the prover client wrapper.

Tests the ScoreInput builder, proof_id generation, subprocess invocation,
and error handling — all via mocking so no real CLI binary is needed.
"""
import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from api.prover_client import (
    _build_score_input,
    _generate_proof_id,
    _serialize_repo,
    _serialize_commit,
    _serialize_issue,
    _serialize_pr,
    _serialize_readme,
    _serialize_cicd,
    _serialize_contribution,
    _TEMP_DIR_PREFIX,
    PROVER_CLI,
    run_proof,
)


# ---------------------------------------------------------------------------
# Fixtures: mock dataclass-like objects matching the crawler return types
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    """A SimpleNamespace mimicking GitHubRepo."""
    from types import SimpleNamespace
    return SimpleNamespace(
        name="test-repo",
        full_name="testuser/test-repo",
        description="A test repository",
        language="Python",
        stars=42,
        forks=7,
        is_fork=False,
        is_private=False,
        pushed_at="2024-01-15T10:00:00+00:00",
    )


@pytest.fixture
def mock_commit():
    from types import SimpleNamespace
    return SimpleNamespace(
        sha="abc123",
        message="feat: add test feature",
        author="testuser",
        date="2024-01-10T08:00:00+00:00",
        additions=100,
        deletions=20,
    )


@pytest.fixture
def mock_issue():
    from types import SimpleNamespace
    return SimpleNamespace(
        number=1,
        title="Test issue",
        state="CLOSED",
        created_at="2024-01-05T12:00:00+00:00",
        closed_at="2024-01-06T12:00:00+00:00",
        comments=3,
        author="testuser",
    )


@pytest.fixture
def mock_pr():
    from types import SimpleNamespace
    return SimpleNamespace(
        number=5,
        title="Add feature X",
        state="MERGED",
        created_at="2024-01-02T09:00:00+00:00",
        closed_at="2024-01-03T09:00:00+00:00",
        merged_at="2024-01-03T09:30:00+00:00",
        additions=200,
        deletions=50,
        changed_files=4,
        comments=2,
        review_comments=1,
        author="testuser",
    )


@pytest.fixture
def mock_readme():
    from types import SimpleNamespace
    return SimpleNamespace(
        content="# Test\nHello world.",
        size_bytes=30,
        encoding="base64",
        name="README.md",
        detected_sections=["Getting Started", "API"],
        badge_count=1,
        has_code_blocks=True,
        code_block_count=2,
        has_emoji=False,
        list_count=2,
    )


@pytest.fixture
def mock_cicd():
    from types import SimpleNamespace
    return SimpleNamespace(
        path=".github/workflows",
        config_type="github_actions",
        exists=True,
        size_bytes=500,
        content_summary="directory with 2 file(s)",
    )


@pytest.fixture
def mock_contribution():
    from types import SimpleNamespace
    return SimpleNamespace(
        total_contributions=365,
        contribution_years=[2023, 2024],
        contribution_days=[
            SimpleNamespace(date="2024-01-01", contribution_count=5),
            SimpleNamespace(date="2024-01-02", contribution_count=3),
        ],
        weeks_with_contributions=48,
        total_weeks=52,
        first_contribution_date="2023-01-01",
        longest_streak=30,
        current_streak=5,
    )


@pytest.fixture
def mock_activity_data(
    mock_repo, mock_commit, mock_issue, mock_pr,
    mock_readme, mock_cicd, mock_contribution,
):
    """Full activity data dict as returned by GitHubAPIClient.get_user_activity()."""
    return {
        "repos": [mock_repo],
        "commits": [mock_commit, mock_commit],  # second commit as additional
        "issues": [mock_issue],
        "prs": [mock_pr],
        "readmes": {"testuser/test-repo": mock_readme},
        "cicd_configs": {"testuser/test-repo": [mock_cicd]},
        "contributions": mock_contribution,
    }


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


class TestSerializeRepo:
    def test_basic_fields(self, mock_repo):
        result = _serialize_repo(mock_repo)
        assert result["name"] == "test-repo"
        assert result["full_name"] == "testuser/test-repo"
        assert result["language"] == "Python"
        assert result["stars"] == 42
        assert result["is_fork"] is False
        assert result["is_private"] is False

    def test_description_is_none(self):
        from types import SimpleNamespace
        repo = SimpleNamespace(
            name="r", full_name="u/r", description=None, language=None,
            stars=0, forks=0, is_fork=False, is_private=False,
            pushed_at="2024-01-01T00:00:00+00:00",
        )
        result = _serialize_repo(repo)
        assert result["description"] is None
        assert result["language"] is None


class TestSerializeCommit:
    def test_basic_fields(self, mock_commit):
        result = _serialize_commit(mock_commit)
        assert result["sha"] == "abc123"
        assert result["message"] == "feat: add test feature"
        assert result["additions"] == 100


class TestSerializeIssue:
    def test_basic_fields(self, mock_issue):
        result = _serialize_issue(mock_issue)
        assert result["number"] == 1
        assert result["state"] == "CLOSED"
        assert result["comments"] == 3

    def test_closed_at_none(self):
        from types import SimpleNamespace
        issue = SimpleNamespace(
            number=2, title="Open issue", state="OPEN",
            created_at="2024-01-01T00:00:00+00:00",
            closed_at=None, comments=0, author="user",
        )
        result = _serialize_issue(issue)
        assert result["closed_at"] is None


class TestSerializePR:
    def test_basic_fields(self, mock_pr):
        result = _serialize_pr(mock_pr)
        assert result["number"] == 5
        assert result["state"] == "MERGED"
        assert result["additions"] == 200

    def test_merged_at_none(self):
        from types import SimpleNamespace
        pr = SimpleNamespace(
            number=6, title="Open PR", state="OPEN",
            created_at="2024-01-01T00:00:00+00:00",
            closed_at=None, merged_at=None,
            additions=10, deletions=0, changed_files=1,
            comments=0, review_comments=0, author="user",
        )
        result = _serialize_pr(pr)
        assert result["merged_at"] is None
        assert result["closed_at"] is None


class TestSerializeReadme:
    def test_basic_fields(self, mock_readme):
        result = _serialize_readme(mock_readme)
        assert result["name"] == "README.md"
        assert result["has_code_blocks"] is True
        assert result["code_block_count"] == 2


class TestSerializeCicd:
    def test_basic_fields(self, mock_cicd):
        result = _serialize_cicd(mock_cicd)
        assert result["config_type"] == "github_actions"
        assert result["exists"] is True


class TestSerializeContribution:
    def test_none_returns_none(self):
        assert _serialize_contribution(None) is None

    def test_basic_fields(self, mock_contribution):
        result = _serialize_contribution(mock_contribution)
        assert result["total_contributions"] == 365
        assert len(result["contribution_days"]) == 2
        assert result["longest_streak"] == 30


# ---------------------------------------------------------------------------
# _build_score_input
# ---------------------------------------------------------------------------


class TestBuildScoreInput:
    def test_full_conversion(self, mock_activity_data):
        """Full activity data converts to correct ScoreInput structure."""
        result = _build_score_input(mock_activity_data)
        assert "repos" in result
        assert "commits" in result
        assert "issues" in result
        assert "prs" in result
        assert "readmes" in result
        assert "cicd_configs" in result
        assert "contributions" in result
        assert len(result["repos"]) == 1
        assert len(result["commits"]) == 2
        assert result["repos"][0]["name"] == "test-repo"

    def test_empty_activity_data(self):
        """Empty activity data produces empty arrays and None contributions."""
        result = _build_score_input({})
        assert result["repos"] == []
        assert result["commits"] == []
        assert result["issues"] == []
        assert result["prs"] == []
        assert result["readmes"] == {}
        assert result["cicd_configs"] == {}
        assert result["contributions"] is None

    def test_output_is_json_serializable(self, mock_activity_data):
        """ScoreInput dict must be JSON-serializable for the Rust CLI."""
        result = _build_score_input(mock_activity_data)
        json_str = json.dumps(result, default=str)
        parsed = json.loads(json_str)
        assert parsed["repos"][0]["name"] == "test-repo"
        assert len(parsed["commits"]) == 2


# ---------------------------------------------------------------------------
# _generate_proof_id
# ---------------------------------------------------------------------------


class TestGenerateProofId:
    def test_returns_string(self):
        proof_id = _generate_proof_id("testuser")
        assert isinstance(proof_id, str)
        assert proof_id.startswith("proof_")

    def test_length(self):
        proof_id = _generate_proof_id("testuser")
        # proof_ prefix (6) + 16 hex chars = 22 chars
        assert len(proof_id) == 22

    def test_hex_chars_after_proof_prefix(self):
        proof_id = _generate_proof_id("testuser")
        hex_part = proof_id[6:]
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_different_usernames_different_ids(self):
        id_a = _generate_proof_id("user_a")
        id_b = _generate_proof_id("user_b")
        assert id_a != id_b

    def test_deterministic_within_same_call(self):
        """Same username+timestamp sequence yields same format."""
        # Can't test true determinism since timestamp varies, but format is stable
        id1 = _generate_proof_id("sameuser")
        assert id1.startswith("proof_")
        assert len(id1) == 22


# ---------------------------------------------------------------------------
# run_proof — subprocess invocation
# ---------------------------------------------------------------------------


class TestRunProof:
    def test_successful_call(self, mock_activity_data):
        """Happy path: CLI succeeds and returns metadata."""
        fake_stdout = json.dumps({
            "status": "proof_generated",
            "proving_time_ms": 12345,
            "proving_time_seconds": 12.345,
            "prover": "local",
        })

        with (
            patch("api.prover_client.subprocess.run") as mock_run,
            patch("api.prover_client.os.path.isfile") as mock_isfile,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=fake_stdout,
                stderr="",
            )
            mock_isfile.return_value = True

            result = run_proof("testuser", mock_activity_data, timeout=30)

        assert result["status"] == "proof_generated"
        assert result["proof_id"].startswith("proof_")
        assert result["proving_time_ms"] == 12345
        assert result["prover"] == "local"
        assert result["proof_path"] is not None
        assert "input_summary" in result
        assert result["input_summary"]["repos"] == 1

        # Verify the CLI was called with --input and a temp file
        args, kwargs = mock_run.call_args
        cli_args = args[0]
        assert cli_args[0] == PROVER_CLI
        assert cli_args[1] == "--input"
        assert cli_args[2].endswith(".json")

    def test_cli_failure(self, mock_activity_data):
        """Non-zero exit code returns proof_failed status."""
        with patch("api.prover_client.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Invalid input JSON",
            )

            result = run_proof("testuser", mock_activity_data, timeout=30)

        assert result["status"] == "proof_failed"
        assert "error" in result
        assert "Invalid input JSON" in result["error"]
        assert result["proof_path"] is None

    def test_binary_not_found(self, mock_activity_data):
        """FileNotFoundError when CLI binary doesn't exist."""
        with patch("api.prover_client.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError(
                "No such file or directory: 'scoring-prover-cli'"
            )

            with pytest.raises(FileNotFoundError):
                run_proof("testuser", mock_activity_data, timeout=30)

    def test_timeout(self, mock_activity_data):
        """TimeoutExpired when subprocess takes too long."""
        with patch("api.prover_client.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd="scoring-prover-cli", timeout=30
            )

            with pytest.raises(subprocess.TimeoutExpired):
                run_proof("testuser", mock_activity_data, timeout=30)

    def test_non_json_stdout_is_handled(self, mock_activity_data):
        """When stdout is not valid JSON, fall back to elapsed timing."""
        with (
            patch("api.prover_client.subprocess.run") as mock_run,
            patch("api.prover_client.os.path.isfile") as mock_isfile,
            patch("api.prover_client.time.monotonic") as mock_time,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[sp1-script] Some log output\nMore log output\n",
                stderr="",
            )
            mock_isfile.return_value = True
            # Return consistent time values so elapsed_ms > 0
            mock_time.side_effect = [1000.0, 1012.345]

            result = run_proof("testuser", mock_activity_data, timeout=30)

        # Should not crash; falls back to elapsed timing
        assert result["status"] == "proof_generated"
        assert result["proving_time_ms"] > 0
        assert result["proof_path"] is not None

    def test_input_summary_in_result(self, mock_activity_data):
        """Result includes a useful input_summary."""
        with patch("api.prover_client.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"status": "proof_generated"}),
                stderr="",
            )

            result = run_proof("testuser", mock_activity_data, timeout=30)

        summary = result["input_summary"]
        assert summary["repos"] == 1
        assert summary["commits"] == 2
        assert summary["issues"] == 1
        assert summary["prs"] == 1
        assert summary["readmes"] == 1

    def test_proof_path_none_when_file_missing(self, mock_activity_data):
        """proof_path is None when no proof file is found."""
        with (
            patch("api.prover_client.subprocess.run") as mock_run,
            patch("api.prover_client.os.path.isfile") as mock_isfile,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"status": "proof_generated"}),
                stderr="",
            )
            mock_isfile.return_value = False

            result = run_proof("testuser", mock_activity_data, timeout=30)

        assert result["proof_path"] is None
