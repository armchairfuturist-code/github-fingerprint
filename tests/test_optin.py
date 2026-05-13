"""
Tests for the GitHub opt-in flow (landing page, analyze, redirect).
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.main import app


MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}


class TestLandingPage:
    """Tests for the landing page served at GET /."""

    def test_landing_page_renders(self):
        """GET / should return 200 with HTML containing analyze input."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert 'id="analyze-input"' in response.text
        assert 'id="analyze-btn"' in response.text
        assert "Analyze" in response.text or "analyze" in response.text

    def test_landing_page_has_value_props(self):
        """Landing page should show value proposition cards."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        # Should show at least one of the value props
        assert any(p in response.text for p in ["Deep Analysis", "ZK-Verified", "Shareable"])

    def test_landing_page_has_advanced_tools(self):
        """Landing page should include the advanced tools section toggle."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "Advanced Tools" in response.text or "advanced" in response.text.lower()


class TestAnalyzeFlow:
    """Tests for the analyze → score → redirect flow."""

    def test_score_endpoint_works_for_analyze(self, monkeypatch):
        """The /score/{username} endpoint used by analyze should work."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        response = client.get("/score/testuser")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "overall_score" in data
        assert "signal_scores" in data

    def test_analyze_flow_on_frontend_redirects(self, monkeypatch):
        """Simulate the frontend analyze flow: fetch /score then verify redirect target."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)

        # Step 1: Score the user
        score_res = client.get("/score/flowuser")
        assert score_res.status_code == 200

        # Step 2: The frontend would redirect to /u/flowuser
        profile_res = client.get("/u/flowuser")
        assert profile_res.status_code == 200
        assert "flowuser" in profile_res.text

    def test_analyze_invalid_user_shows_error(self, monkeypatch):
        """Invalid username in analyze should return 400 and not 500."""
        mock_client = MagicMock()
        mock_client.get_user_activity.side_effect = ValueError("User not found")
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/score/nonexistent")

        assert response.status_code == 400

    def test_profile_page_exists_after_analyze(self, monkeypatch):
        """After a successful score, the profile page should be accessible."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = {
            **MINIMAL_ACTIVITY,
            "public_repos": 8,
            "followers": 15,
        }
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)

        # Score the user
        score_res = client.get("/score/analyzeme")
        assert score_res.status_code == 200

        # Verify profile page exists with correct stats
        profile_res = client.get("/u/analyzeme")
        assert profile_res.status_code == 200
        assert "8 repos" in profile_res.text
        assert "15 followers" in profile_res.text
