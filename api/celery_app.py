"""
Celery app configuration for async proof generation.

Uses Redis as both broker and result backend. Configuration is driven
by environment variables with sensible defaults for local development.

Environment variables:
    REDIS_URL       Redis connection URL (default: redis://localhost:6379/0)
    CELERY_WORKER_CONCURRENCY  Worker concurrency (default: 2)
"""
import logging
import os
from celery import Celery

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis / Broker configuration
# ---------------------------------------------------------------------------

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_WORKER_CONCURRENCY = int(os.environ.get("CELERY_WORKER_CONCURRENCY", "2"))

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------

celery_app = Celery(
    "github_fingerprint",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["api.proof_tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_acks_late=True,  # Re-deliver if worker crashes mid-task
    worker_prefetch_multiplier=1,
    # Default queue
    task_default_queue="proof_generation",
    task_default_exchange="proof_generation",
    task_default_routing_key="proof.generation",
)

logger.info(
    "Celery app configured: broker=%s backend=%s",
    REDIS_URL.rsplit("@", 1)[-1] if "@" in REDIS_URL else REDIS_URL,
    "redis://...",
)
