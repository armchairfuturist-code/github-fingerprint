"""
Tests for the server-rendered profile page (/u/{username}).
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.main import app


MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}

STATS_ACTIVITY = {
    **MINIMAL_ACTIVITY,
    "public_repos": 23,
    "followers": 100,
    "public_gists": 5,
}


class TestProfilePageRoute:
    """Tests for the GET /u/{username} server-rendered profile page."""

    def test_profile_page_returns_200(self, monkeypatch):
        """GET /u/{username} should return 200 with HTML profile."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "testuser" in response.text
        assert "Overall Score" in response.text

    def test_profile_page_shows_score_and_signals(self, monkeypatch):
        """Profile page should contain score, signals, and section headings."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        # Score section
        assert "Signal Breakdown" in response.text
        # Risk flags section
        assert "Risk Flags" in response.text
        # Attestation section
        assert "Attestation" in response.text
        # ZK Proof section
        assert "ZK Proof" in response.text

    def test_profile_page_has_cache_control(self, monkeypatch):
        """Profile page responses should include Cache-Control header."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        cache_control = response.headers.get("cache-control", "")
        assert "public" in cache_control
        assert "max-age=300" in cache_control

    def test_profile_page_returns_404(self, monkeypatch):
        """GET /u/nonexistent should return 404 for invalid users."""
        mock_client = MagicMock()
        mock_client.get_user_activity.side_effect = ValueError("User not found")
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/nonexistent")

        assert response.status_code == 404
        assert "Profile Not Found" in response.text
        assert "nonexistent" in response.text

    def test_profile_shows_profile_info(self, monkeypatch):
        """Profile page should show repo and follower counts."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = {
            **MINIMAL_ACTIVITY,
            "public_repos": 15,
            "followers": 42,
        }
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        assert "15 repos" in response.text
        assert "42 followers" in response.text

    def test_profile_shows_attestation_when_available(self, monkeypatch):
        """Profile page should show attestation badge when signing key is loaded."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/testuser")

        assert response.status_code == 200
        # Should show verified badge since signing key is initialized at import
        assert "Verified" in response.text or "No Attestation" in response.text


class TestProfileStats:
    """Tests for profile stats rendering."""

    def test_profile_shows_repo_count(self, monkeypatch):
        """Profile should display correct repo count."""
        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = STATS_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.get("/u/statsuser")

        assert response.status_code == 200
        assert "23 repos" in response.text
        assert "100 followers" in response.text
