"""
Tests for the Celery app configuration.
"""
from unittest.mock import patch
import pytest


class TestCeleryAppConfig:
    """Verify Celery app is correctly configured."""

    def test_celery_app_imports(self):
        """Celery app module should import cleanly."""
        from api.celery_app import celery_app
        assert celery_app.main == "github_fingerprint"
        assert celery_app.conf.task_serializer == "json"

    def test_celery_app_includes_proof_tasks(self):
        """Celery app should auto-discover proof_tasks."""
        from api.celery_app import celery_app
        assert "api.proof_tasks" in celery_app.conf.include

    def test_celery_app_redis_config(self):
        """Celery app should use Redis as broker and backend."""
        from api.celery_app import celery_app, REDIS_URL
        assert "redis" in REDIS_URL
        assert "6379" in REDIS_URL

    def test_celery_app_default_queue(self):
        """Celery app should default to proof_generation queue."""
        from api.celery_app import celery_app
        assert celery_app.conf.task_default_queue == "proof_generation"

    def test_celery_app_acks_late(self):
        """Celery app should have acks_late for at-least-once delivery."""
        from api.celery_app import celery_app
        assert celery_app.conf.task_acks_late is True

    def test_celery_app_utc_timezone(self):
        """Celery app should use UTC timezone."""
        from api.celery_app import celery_app
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True


class TestRedisUrlFromEnv:
    """Verify REDIS_URL can be set via environment variable."""

    def test_default_redis_url(self):
        """Default REDIS_URL should be localhost."""
        from api.celery_app import REDIS_URL
        assert REDIS_URL == "redis://localhost:6379/0"

    def test_custom_redis_url(self):
        """REDIS_URL should respect environment variable."""
        with patch.dict("os.environ", {"REDIS_URL": "redis://custom:6380/1"}):
            # Re-import to pick up new env var
            import importlib
            import api.celery_app as ca
            importlib.reload(ca)
            assert ca.REDIS_URL == "redis://custom:6380/1"
        # Reload back to default
        import importlib
        import api.celery_app as ca
        importlib.reload(ca)
