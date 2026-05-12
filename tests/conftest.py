"""
Pytest configuration and shared fixtures for the GitHub Fingerprint test suite.

Provides automatic mocking of Celery/Redis ``enqueue_proof`` to prevent
test hangs when Redis is not running. All tests that exercise the FastAPI
endpoints will have ``enqueue_proof`` patched to return a mock task ID.
"""
import pytest


@pytest.fixture(autouse=True)
def _mock_enqueue_proof(monkeypatch):
    """Automatically mock ``api.main.enqueue_proof`` in every test.

    This prevents the Celery task from attempting to connect to Redis
    during test execution. Tests that specifically need to verify Celery
    behavior can override this fixture by providing their own mock.
    """
    monkeypatch.setattr(
        "api.main.enqueue_proof",
        lambda *args, **kwargs: "mock-task-id",
    )
