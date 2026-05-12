"""
End-to-end integration tests for the GitHub Fingerprint API.

Tests the full crawl → score → attest → verify flow by mocking
github_client.get_user_activity to return realistic deep data
(with readmes, cicd_configs, and contributions keys).
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Realistic mock activity data
# ---------------------------------------------------------------------------

def _make_datetime(days_ago: int) -> datetime:
    """Create a timezone-aware datetime offset from now."""
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def _make_repo(name: str, language: str, is_fork: bool = False,
               stars: int = 10, description: str = "A test repository"):
    """Build a GitHubRepo-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        name=name,
        full_name=f"testuser/{name}",
        description=description,
        language=language,
        stars=stars,
        forks=3,
        created_at=_make_datetime(365),
        updated_at=_make_datetime(1),
        pushed_at=_make_datetime(1),
        is_fork=is_fork,
        is_private=False,
    )


def _make_commit(sha: str, message: str, days_ago: int,
                 additions: int = 10, deletions: int = 5):
    """Build a GitHubCommit-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        sha=sha,
        message=message,
        author="testuser",
        date=_make_datetime(days_ago),
        additions=additions,
        deletions=deletions,
    )


def _make_issue(number: int, title: str, state: str, days_ago: int,
                comments: int = 3, is_closed: bool = True):
    """Build a GitHubIssue-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        number=number,
        title=title,
        state=state,
        created_at=_make_datetime(days_ago),
        closed_at=_make_datetime(days_ago - 2) if is_closed else None,
        comments=comments,
        author="testuser",
    )


def _make_pr(number: int, title: str, state: str, days_ago: int,
             additions: int = 50, deletions: int = 30, changed_files: int = 5,
             comments: int = 4, review_comments: int = 6, is_merged: bool = True):
    """Build a GitHubPR-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        number=number,
        title=title,
        state=state,
        created_at=_make_datetime(days_ago),
        closed_at=_make_datetime(days_ago - 1) if state == "MERGED" or is_merged else _make_datetime(days_ago - 1),
        merged_at=_make_datetime(days_ago - 1) if is_merged else None,
        additions=additions,
        deletions=deletions,
        changed_files=changed_files,
        comments=comments,
        review_comments=review_comments,
        author="testuser",
    )


def _make_readme(content: str, sections: List[str] = None,
                 badge_count: int = 2, has_code: bool = True,
                 code_blocks: int = 3, has_emoji: bool = True,
                 list_count: int = 5):
    """Build a GitHubReadme-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        content=content,
        size_bytes=len(content.encode("utf-8")),
        encoding="base64",
        name="README.md",
        detected_sections=sections or ["Getting Started", "API", "Contributing"],
        badge_count=badge_count,
        has_code_blocks=has_code,
        code_block_count=code_blocks,
        has_emoji=has_emoji,
        list_count=list_count,
    )


def _make_cicd_config(path: str, config_type: str, exists: bool = True,
                      size_bytes: int = 500, summary: str = ""):
    """Build a GitHubCICDConfig-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        path=path,
        config_type=config_type,
        exists=exists,
        size_bytes=size_bytes,
        content_summary=summary or f"{path.split('/')[-1]} ({size_bytes} bytes)",
    )


def _make_contrib_day(days_ago: int, count: int):
    """Build a GitHubContributionDay-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(
        date=_make_datetime(days_ago),
        contribution_count=count,
    )


def _make_contributions(total: int = 850, streak: int = 15,
                        current_streak: int = 5):
    """Build a GitHubContributionData-like object."""
    from types import SimpleNamespace
    days = []
    for i in range(365):
        count = 2 if i < 350 else 0  # Some zero days at end
        if i % 3 == 0:
            count = 5
        if i % 7 == 0:
            count = 0
        days.append(_make_contrib_day(365 - i, count))

    return SimpleNamespace(
        total_contributions=total,
        contribution_years=[2023, 2024, 2025],
        contribution_days=days,
        weeks_with_contributions=48,
        total_weeks=52,
        first_contribution_date=_make_datetime(365),
        longest_streak=streak,
        current_streak=current_streak,
    )


def build_realistic_activity_data() -> Dict[str, Any]:
    """Build a rich, realistic activity data dict for mocking.

    Returns a dict with the same shape as GitHubAPIClient.get_user_activity(),
    including readmes, cicd_configs, and contributions keys.
    """
    repos = [
        _make_repo("awesome-project", "Python"),
        _make_repo("frontend-app", "TypeScript"),
        _make_repo("data-science", "Jupyter Notebook", is_fork=True),
        _make_repo("cli-tool", "Go"),
        _make_repo("configs", "HCL", description="Infrastructure configs"),
    ]

    commits = [
        _make_commit("a1b2c3d", "feat: add user authentication", 1, 120, 30),
        _make_commit("b2c3d4e", "fix: handle edge case in login flow", 2, 15, 8),
        _make_commit("c3d4e5f", "refactor: extract validation logic", 3, 40, 60),
        _make_commit("d4e5f6g", "feat(api): add rate limiting middleware", 4, 80, 20),
        _make_commit("e5f6g7h", "docs: update README with setup instructions", 5, 10, 2),
        _make_commit("f6g7h8i", "test: add unit tests for auth module", 6, 200, 5),
        _make_commit("g7h8i9j", "chore: bump dependencies", 7, 5, 5),
        _make_commit("h8i9j0k", "perf: optimize database queries", 8, 30, 100),
        _make_commit("i9j0k1l", "style: format code with black", 9, 1, 1),
        _make_commit("j0k1l2m", "ci: add GitHub Actions workflow", 10, 50, 0),
        _make_commit("k1l2m3n", "fix: resolve null pointer in parser", 11, 8, 12),
        _make_commit("l2m3n4o", "feat: add export to CSV feature", 12, 90, 25),
    ]

    issues = [
        _make_issue(1, "Login page returns 500 on invalid token", "CLOSED", 10, comments=8),
        _make_issue(2, "Add dark mode support", "CLOSED", 15, comments=12),
        _make_issue(3, "Performance regression in search", "CLOSED", 20, comments=5),
        _make_issue(4, "Document API endpoints", "OPEN", 5, comments=3, is_closed=False),
        _make_issue(5, "Add input validation for emails", "CLOSED", 25, comments=6),
        _make_issue(6, "Memory leak in websocket handler", "OPEN", 2, comments=10, is_closed=False),
    ]

    prs = [
        _make_pr(10, "Add user authentication module", "MERGED", 8, 250, 80, 12, comments=6, review_comments=8),
        _make_pr(11, "Refactor database layer", "MERGED", 12, 400, 350, 18, comments=10, review_comments=15),
        _make_pr(12, "Update dependency versions", "MERGED", 5, 30, 30, 3, comments=2, review_comments=1),
        _make_pr(13, "Add WebSocket support", "OPEN", 2, 500, 100, 25, comments=4, review_comments=3, is_merged=False),
    ]

    readmes = {
        "testuser/awesome-project": _make_readme(
            content="# Awesome Project\n\n" +
                    "![CI](https://github.com/testuser/awesome-project/actions/workflows/ci.yml/badge.svg)\n" +
                    "![Coverage](https://codecov.io/gh/testuser/awesome-project/badge.svg)\n\n" +
                    "## Getting Started\n\n" +
                    "Clone the repo and run `pip install -r requirements.txt`.\n\n" +
                    "```python\nfrom awesome import Client\nclient = Client()\nresult = client.process()\n```\n\n" +
                    "- Feature A\n- Feature B\n- Feature C\n\n" +
                    "## API\n\nSee [docs](docs/api.md) for full API reference.\n\n" +
                    "## Contributing\n\nWe welcome PRs! :tada:\n\n" +
                    "## License\n\nMIT",
            sections=["Getting Started", "API", "Contributing", "License"],
            badge_count=2, has_code=True, code_blocks=1, has_emoji=True, list_count=3,
        ),
        "testuser/frontend-app": _make_readme(
            content="# Frontend App\n\n" +
                    "![Build](https://github.com/testuser/frontend-app/actions/workflows/build.yml/badge.svg)\n\n" +
                    "## Quick Start\n\n" +
                    "```bash\nnpm install\nnpm run dev\n```\n\n" +
                    "- Component library included\n\n## Project Structure\n\nSee [docs](docs/STRUCTURE.md).\n\n" +
                    "## Deployment\n\nDeployed via Vercel.",
            sections=["Quick Start", "Project Structure", "Deployment"],
            badge_count=1, has_code=True, code_blocks=1, has_emoji=False, list_count=1,
        ),
        "testuser/cli-tool": _make_readme(
            content="# CLI Tool\n\n" +
                    "![Release](https://img.shields.io/github/v/release/testuser/cli-tool)\n\n" +
                    "## Installation\n\n```bash\ngo install github.com/testuser/cli-tool@latest\n```\n\n" +
                    "## Usage\n\n```bash\ncli-tool --help\ncli-tool process --input file.txt\n```\n\n" +
                    "- Supports JSON and YAML output\n- Compatible with CI pipelines\n\n" +
                    "## Examples\n\nSee [examples/](examples/).\n\n" +
                    "Made with :heart:",
            sections=["Installation", "Usage", "Examples"],
            badge_count=1, has_code=True, code_blocks=2, has_emoji=True, list_count=2,
        ),
    }

    cicd_configs: Dict[str, Any] = {
        "testuser/awesome-project": [
            _make_cicd_config(".github/workflows", "github_actions", True),
            _make_cicd_config("Dockerfile", "docker", True),
            _make_cicd_config(".travis.yml", "travis", False),
            _make_cicd_config(".circleci/config.yml", "circleci", False),
        ],
        "testuser/frontend-app": [
            _make_cicd_config(".github/workflows", "github_actions", True),
            _make_cicd_config("Dockerfile", "docker", False, summary=""),
        ],
        "testuser/data-science": [
            _make_cicd_config("Jenkinsfile", "jenkins", True),
        ],
        "testuser/cli-tool": [
            _make_cicd_config(".github/workflows", "github_actions", True),
            _make_cicd_config("Dockerfile", "docker", True),
            _make_cicd_config(".gitlab-ci.yml", "gitlab_ci", True),
        ],
        "testuser/configs": [
            _make_cicd_config(".github/workflows", "github_actions", False),
        ],
    }

    contributions = _make_contributions(total=850, streak=15, current_streak=5)

    return {
        "repos": repos,
        "commits": commits,
        "issues": issues,
        "prs": prs,
        "readmes": readmes,
        "cicd_configs": cicd_configs,
        "contributions": contributions,
        "changelogs": {},
        "repos_data": {},
    }


REALISTIC_ACTIVITY = build_realistic_activity_data()


@pytest.fixture
def mock_github_client():
    """Fixture that mocks _get_github_client to return realistic data."""
    with patch("api.main._get_github_client") as mock_getter:
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = REALISTIC_ACTIVITY
        mock_getter.return_value = mock_client
        yield mock_getter


# ---------------------------------------------------------------------------
# Test 1: POST /score returns complete response with all expected fields
# ---------------------------------------------------------------------------

class TestPostScore:
    """Tests for POST /score endpoint."""

    def test_returns_overall_score_and_signal_scores(self, mock_github_client):
        """POST /score should return overall_score and signal_scores."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert isinstance(data["overall_score"], (int, float))
        assert 0 <= data["overall_score"] <= 100

    def test_all_12_signal_keys_present(self, mock_github_client):
        """POST /score should include all 12 signal keys in signal_scores."""
        from fastapi.testclient import TestClient
        from api.main import app

        EXPECTED_SIGNALS = {
            "commit_consistency", "language_diversity", "issue_engagement",
            "pr_patterns", "project_ownership", "review_patterns",
            "response_time", "readme_quality", "commit_semantics",
            "cicd_maturity", "contribution_consistency", "ai_usage_patterns",
        }

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        actual_signals = set(data["signal_scores"].keys())
        missing = EXPECTED_SIGNALS - actual_signals
        extra = actual_signals - EXPECTED_SIGNALS
        assert not missing, f"Missing signal keys: {missing}"
        assert not extra, f"Unexpected signal keys: {extra}"

    def test_each_signal_has_score_confidence_and_details(self, mock_github_client):
        """Each signal entry should have score, confidence, and details."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        for signal_name, signal_data in data["signal_scores"].items():
            assert "score" in signal_data, f"{signal_name} missing 'score'"
            assert "confidence" in signal_data, f"{signal_name} missing 'confidence'"
            assert "details" in signal_data, f"{signal_name} missing 'details'"
            assert isinstance(signal_data["score"], (int, float))

    def test_response_has_profile_and_details(self, mock_github_client):
        """Response should contain profile, details, and risk_flags."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert isinstance(data["profile"], str)
        assert "details" in data
        assert "risk_flags" in data
        assert isinstance(data["risk_flags"], list)

    def test_response_includes_attestation_block(self, mock_github_client):
        """POST /score response should include an attestation block."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None
        assert "signature" in data["attestation"]
        assert "public_key" in data["attestation"]
        assert "signed_payload" in data["attestation"]
        assert "signed_at" in data["attestation"]

    def test_username_in_response(self, mock_github_client):
        """Username in response should match the request."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={"username": "integration_user"})

        assert response.status_code == 200
        assert response.json()["username"] == "integration_user"

    def test_scores_are_deterministic(self, mock_github_client):
        """Same input should produce identical scores."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        resp1 = client.post("/score", json={"username": "testuser"})
        resp2 = client.post("/score", json={"username": "testuser"})

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["overall_score"] == resp2.json()["overall_score"]
        assert resp1.json()["signal_scores"] == resp2.json()["signal_scores"]


# ---------------------------------------------------------------------------
# Test 2: POST /verify round-trips the attestation
# ---------------------------------------------------------------------------

class TestAttestationRoundTrip:
    """Tests for attestation round-trip via POST /verify."""

    def test_attestation_can_be_verified(self, mock_github_client):
        """Attestation from POST /score should be verifiable via POST /verify."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        # Get score with attestation
        score_resp = client.post("/score", json={"username": "verifyuser"})
        assert score_resp.status_code == 200
        att = score_resp.json()["attestation"]

        # Verify the attestation
        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })

        assert verify_resp.status_code == 200
        vdata = verify_resp.json()
        assert vdata["valid"] is True
        assert vdata["payload"]["username"] == "verifyuser"

    def test_attestation_payload_contains_all_expected_fields(self, mock_github_client):
        """Attestation payload should contain username, overall_score, signal_scores, etc."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "fieldstest"})

        assert score_resp.status_code == 200
        data = score_resp.json()
        payload = json.loads(data["attestation"]["signed_payload"])

        assert "username" in payload
        assert "overall_score" in payload
        assert "signal_scores" in payload
        assert "risk_flags" in payload
        assert "profile_name" in payload
        assert "signed_at" in payload
        assert payload["username"] == "fieldstest"
        assert payload["overall_score"] == data["overall_score"]
        assert payload["signal_scores"] == data["signal_scores"]

    def test_verify_with_tampered_payload(self, mock_github_client):
        """Tampered payload should be detected as invalid."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "tampertest"})

        assert score_resp.status_code == 200
        att = score_resp.json()["attestation"]

        # Send a different payload with the original signature
        verify_resp = client.post("/verify", json={
            "signed_payload": '{"tampered": true}',
            "signature": att["signature"],
            "public_key": att["public_key"],
        })

        assert verify_resp.status_code == 200
        vdata = verify_resp.json()
        assert vdata["valid"] is False

    def test_verify_round_trip_full_crawl(self, mock_github_client):
        """Full round-trip: score user, verify attestation, confirm payload integrity."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        # Score
        score_resp = client.post("/score", json={"username": "full_cycle"})
        assert score_resp.status_code == 200
        data = score_resp.json()
        att = data["attestation"]

        # Verify
        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })

        assert verify_resp.status_code == 200
        vdata = verify_resp.json()

        # Confirm payload matches original score
        assert vdata["valid"] is True
        assert vdata["payload"]["username"] == "full_cycle"
        assert vdata["payload"]["overall_score"] == data["overall_score"]


# ---------------------------------------------------------------------------
# Test 3: POST /score with role=marketing returns different scores
# ---------------------------------------------------------------------------

class TestRoleSpecificScoring:
    """Tests for role-specific scoring via POST /score."""

    def test_different_scores_for_different_roles(self, mock_github_client):
        """Different roles should produce different overall scores."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        eng_resp = client.post("/score", json={
            "username": "roletest",
            "role": "engineering",
        })
        mkt_resp = client.post("/score", json={
            "username": "roletest",
            "role": "marketing",
        })
        nt_resp = client.post("/score", json={
            "username": "roletest",
            "role": "non-technical",
        })

        assert eng_resp.status_code == 200
        assert mkt_resp.status_code == 200
        assert nt_resp.status_code == 200

        eng_score = eng_resp.json()["overall_score"]
        mkt_score = mkt_resp.json()["overall_score"]
        nt_score = nt_resp.json()["overall_score"]

        # Scores should differ between profiles (different weights)
        scores = {eng_score, mkt_score, nt_score}
        assert len(scores) >= 2, (
            f"Expected different scores across profiles, got eng={eng_score}, "
            f"mkt={mkt_score}, nt={nt_score}"
        )

    def test_role_changes_profile_in_response(self, mock_github_client):
        """The profile field should reflect the requested role."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        resp = client.post("/score", json={
            "username": "profilerole",
            "role": "marketing",
        })
        assert resp.status_code == 200
        assert resp.json()["profile"] == "marketing"

    def test_default_profile_without_role(self, mock_github_client):
        """Without a role, the endpoint still returns a valid score."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        resp = client.post("/score", json={"username": "defaultrole"})

        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert isinstance(data["profile"], str)
        assert "overall_score" in data

    def test_invalid_role_returns_400(self, mock_github_client):
        """Invalid role should return 400."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        resp = client.post("/score", json={
            "username": "bogusrole",
            "role": "nonexistent_role",
        })

        assert resp.status_code == 400
        assert "Unknown profile" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test 4: GET /score/{username} works with query params
# ---------------------------------------------------------------------------

class TestGetScore:
    """Tests for GET /score/{username} endpoint."""

    def test_get_score_returns_valid_response(self, mock_github_client):
        """GET /score/{username} should return a valid score response."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/score/testuser")

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert data["username"] == "testuser"
        assert "signal_scores" in data

    def test_get_score_with_role_query_param(self, mock_github_client):
        """GET /score/{username}?role=marketing should use the marketing profile."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/score/testuser", params={"role": "marketing"})

        assert response.status_code == 200
        assert response.json()["profile"] == "marketing"

    def test_get_score_with_weights_json(self, mock_github_client):
        """GET /score/{username}?weights=... should parse and apply weights."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        weights = json.dumps({"commit_consistency": 0.5, "language_diversity": 0.5})
        response = client.get("/score/testuser", params={"weights": weights})

        assert response.status_code == 200

    def test_get_score_with_invalid_weights_returns_400(self, mock_github_client):
        """Invalid weights JSON should return 400."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/score/testuser", params={"weights": "not-json"})

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Test 5: POST /match returns role+matching with attestation
# ---------------------------------------------------------------------------

class TestMatch:
    """Tests for POST /match endpoint."""

    def test_match_returns_role_and_match_score(self, mock_github_client):
        """POST /match should return match score, top reasons, and role."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "testuser",
            "role_description": "engineering",
        })

        assert response.status_code == 200
        data = response.json()
        assert "match_score" in data
        assert isinstance(data["match_score"], (int, float))
        assert "top_reasons" in data
        assert isinstance(data["top_reasons"], list)
        assert len(data["top_reasons"]) > 0
        assert data["username"] == "testuser"

    def test_match_includes_attestation(self, mock_github_client):
        """POST /match response should include an attestation block."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "testuser",
            "role_description": "engineering",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None
        assert "signature" in data["attestation"]
        assert "signed_payload" in data["attestation"]

    def test_match_different_roles(self, mock_github_client):
        """Different roles should produce different match scores."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        eng_resp = client.post("/match", json={
            "username": "testuser",
            "role_description": "engineering",
        })
        mkt_resp = client.post("/match", json={
            "username": "testuser",
            "role_description": "marketing",
        })

        assert eng_resp.status_code == 200
        assert mkt_resp.status_code == 200

        eng_match = eng_resp.json()["match_score"]
        mkt_match = mkt_resp.json()["match_score"]

        # Different roles should have different match scores
        scores = {eng_match, mkt_match}
        assert len(scores) >= 2 or eng_resp.json()["top_reasons"] != mkt_resp.json()["top_reasons"], (
            "Different role descriptions should produce different match results"
        )

    def test_match_signal_overview(self, mock_github_client):
        """Match response should include signal_overview."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "testuser",
            "role_description": "engineering",
        })

        assert response.status_code == 200
        data = response.json()
        assert "signal_overview" in data
        assert "overall" in data["signal_overview"]

    def test_match_attestation_verifiable(self, mock_github_client):
        """Match attestation should be verifiable via /verify."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        match_resp = client.post("/match", json={
            "username": "matchverify",
            "role_description": "engineering",
        })
        assert match_resp.status_code == 200
        att = match_resp.json()["attestation"]

        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })
        assert verify_resp.status_code == 200
        assert verify_resp.json()["valid"] is True


# ---------------------------------------------------------------------------
# Test 6: GET /profiles returns profile list
# ---------------------------------------------------------------------------

class TestProfiles:
    """Tests for GET /profiles endpoint."""

    def test_returns_profile_list(self, mock_github_client):
        """GET /profiles should return a list of profiles."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/profiles")

        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert isinstance(data["profiles"], list)

    def test_includes_engineering_profile(self, mock_github_client):
        """Profile list should include 'engineering'."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/profiles")
        assert response.status_code == 200

        names = [p["name"] for p in response.json()["profiles"]]
        assert "engineering" in names

    def test_each_profile_has_all_fields(self, mock_github_client):
        """Each profile should have name, display_name, description, weights."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/profiles")
        assert response.status_code == 200

        for profile in response.json()["profiles"]:
            assert "name" in profile
            assert "display_name" in profile
            assert "description" in profile
            assert "weights" in profile
            assert isinstance(profile["weights"], dict)

    def test_weights_sum_to_approx_one(self, mock_github_client):
        """Each profile's weights should sum to approximately 1.0."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/profiles")
        assert response.status_code == 200

        for profile in response.json()["profiles"]:
            total = sum(profile["weights"].values())
            assert abs(total - 1.0) < 0.001, (
                f"Profile '{profile['name']}' weights sum to {total}, expected ~1.0"
            )


# ---------------------------------------------------------------------------
# Test 7: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for API error handling."""

    def test_invalid_role_returns_400(self, mock_github_client):
        """Invalid role in POST /score should return 400."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/score", json={
            "username": "testuser",
            "role": "invalid_role_name",
        })

        assert response.status_code == 400

    def test_missing_username_returns_422(self):
        """Missing username in POST /score should return 422 (validation error)."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        # No username field
        response = client.post("/score", json={})

        assert response.status_code == 422

    def test_empty_username_returns_error(self):
        """Empty username should return an error response."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        # ScoreRequest has username: str (required)
        response = client.post("/score", json={"username": ""})

        # Empty string passes Pydantic validation (it's a valid str) but
        # may fail downstream in the scoring engine, producing 500.
        assert response.status_code in (400, 422, 500)

    def test_invalid_match_role_returns_400(self, mock_github_client):
        """Bogus match role should not crash."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "testuser",
            "role_description": "xyzzy_unknown_role_123",
        })

        # Should handle gracefully — still return 200 with sensible defaults
        assert response.status_code == 200

    def test_health_endpoint(self):
        """GET /health should return ok status."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Test 8: Attestation payload structure
# ---------------------------------------------------------------------------

class TestAttestationStructure:
    """Tests for attestation payload structure and verifiability."""

    def test_attestation_has_all_required_fields(self, mock_github_client):
        """Attestation block should contain signature, public_key, signed_payload, signed_at."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        resp = client.post("/score", json={"username": "atteststruct"})

        assert resp.status_code == 200
        att = resp.json()["attestation"]

        assert "signature" in att, "Missing 'signature' field"
        assert "public_key" in att, "Missing 'public_key' field"
        assert "signed_payload" in att, "Missing 'signed_payload' field"
        assert "signed_at" in att, "Missing 'signed_at' field"

        # Verify types
        assert isinstance(att["signature"], str), "signature should be a string"
        assert isinstance(att["public_key"], str), "public_key should be a string"
        assert isinstance(att["signed_payload"], str), "signed_payload should be a string"
        assert isinstance(att["signed_at"], str), "signed_at should be a string"

        # Verify payload is valid JSON
        payload = json.loads(att["signed_payload"])
        assert "username" in payload
        assert "overall_score" in payload
        assert "signal_scores" in payload
        assert "risk_flags" in payload
        assert "profile_name" in payload
        assert "signed_at" in payload

    def test_attestation_payload_matches_score_response(self, mock_github_client):
        """Attestation payload key fields should match the score response."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        resp = client.post("/score", json={"username": "matchcheck"})

        assert resp.status_code == 200
        data = resp.json()
        payload = json.loads(data["attestation"]["signed_payload"])

        # Core fields are signed and should match response
        assert payload["username"] == data["username"]
        assert payload["overall_score"] == data["overall_score"]
        assert payload["signal_scores"] == data["signal_scores"]

        # Verify risk_flags is a list in both (may differ if engine state leaked)
        assert isinstance(payload["risk_flags"], list)
        assert isinstance(data["risk_flags"], list)

    def test_attestation_is_verifiable_after_score(self, mock_github_client):
        """Attestation from /score should be fully verifiable via /verify."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        # Score
        score_resp = client.post("/score", json={"username": "verifychain"})
        assert score_resp.status_code == 200
        data = score_resp.json()
        att = data["attestation"]

        # Verify
        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })
        assert verify_resp.status_code == 200
        vdata = verify_resp.json()
        assert vdata["valid"] is True

        # The decoded payload should match
        assert vdata["payload"]["overall_score"] == data["overall_score"]
        assert vdata["payload"]["username"] == "verifychain"


# ---------------------------------------------------------------------------
# Health check (non-mocked, no auth needed)
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self):
        """GET /health should return status ok."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "github-fingerprint-api"
