"""
Celery tasks for async proof generation via the SP1 prover CLI.

Provides a single public task: ``generate_proof``, which calls
``run_proof()`` from the prover client and updates the proof status
store through its lifecycle.

The task is configured with:
    - 3 retries with exponential backoff (max 10 min between retries)
    - Jitter to avoid thundering-herd on recovery
    - Late acknowledgment (task re-delivered if worker crashes)
"""
import json
import logging
from typing import Any, Dict, Optional

from celery import Task
from celery.utils.log import get_task_logger

from .celery_app import celery_app
from .prover_client import run_proof
from .proof_status import get_store

# Use Celery's logger for worker visibility
logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# Base task with retry configuration
# ---------------------------------------------------------------------------


class ProofTaskBase(Task):
    """Base task class with retry defaults for proof generation.

    - autoretry_for: retry on ANY exception (network error, CLI crash, timeout)
    - max_retries: 3 attempts total
    - retry_backoff: exponential backoff (2s, 4s, 8s, ...)
    - retry_backoff_max: cap at 600 seconds (10 minutes)
    - retry_jitter: random jitter to spread retries
    """

    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


# ---------------------------------------------------------------------------
# Proof generation task
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    base=ProofTaskBase,
    name="generate_proof",
    queue="proof_generation",
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_proof(
    self,
    username: str,
    activity_data: dict,
    proof_id: str,
) -> dict:
    """Generate a proof for a user's scoring data.

    This task is enqueued by the ``/score`` endpoint after computing the
    score and returning the response. It runs asynchronously in the Celery
    worker.

    Args:
        username: GitHub username (for proof_id and diagnostics).
        activity_data: Crawl result dict from
            ``GitHubAPIClient.get_user_activity()``.
        proof_id: Pre-generated proof identifier (from
            ``_generate_proof_id()``).

    Returns:
        Proof metadata dict (same shape as ``run_proof()`` return value).
        On failure after exhausting retries, the task still returns a
        proof_failed status dict (it does not re-raise after max retries).

    Raises:
        The task re-raises on each retry attempt. After max_retries are
        exhausted, the task terminates with the last exception and the
        proof status is set to ``failed``.
    """
    store = get_store()
    logger.info(
        "proof_task: proof_id=%s username=%s attempt=%d task_id=%s",
        proof_id,
        username,
        self.request.retries,
        self.request.id,
    )

    # Transition to proof_generating on first attempt
    if self.request.retries == 0:
        store.set_status(
            proof_id,
            "proof_generating",
            username=username,
        )

    try:
        # Run the SP1 prover CLI
        result = run_proof(username, activity_data)

        if result.get("status") == "proof_generated":
            store.set_status(
                proof_id,
                "proof_generated",
                proof_path=result.get("proof_path"),
                metadata={
                    "proving_time_ms": result.get("proving_time_ms"),
                    "proving_time_seconds": result.get("proving_time_seconds"),
                    "prover": result.get("prover"),
                    "input_summary": result.get("input_summary"),
                },
            )
            logger.info(
                "proof_task: proof_id=%s COMPLETED proving_time_ms=%d "
                "attempts=%d",
                proof_id,
                result.get("proving_time_ms", 0),
                self.request.retries + 1,
            )
        else:
            # CLI returned non-zero exit
            error_msg = result.get("error", "proof_failed with no error message")
            store.set_status(proof_id, "failed", error=error_msg, metadata=result)
            logger.error(
                "proof_task: proof_id=%s FAILED (CLI): %s",
                proof_id,
                error_msg,
            )

        return result

    except Exception as exc:
        # Log the failure and store it
        error_msg = f"{type(exc).__name__}: {exc}"
        store.set_status(proof_id, "failed", error=error_msg)
        logger.error(
            "proof_task: proof_id=%s EXCEPTION attempt=%d/%d: %s",
            proof_id,
            self.request.retries + 1,
            self.max_retries + 1,
            error_msg,
        )

        # Re-raise so Celery's autoretry_for handles retry scheduling
        raise


# ---------------------------------------------------------------------------
# Utility: enqueue a proof generation task from the API layer
# ---------------------------------------------------------------------------


def enqueue_proof(username: str, activity_data: dict, proof_id: str) -> str:
    """Enqueue a proof generation task and return the Celery task ID.

    This is the public entry point called from ``main.py`` after the
    ``/score`` endpoint returns its response.

    Args:
        username: GitHub username.
        activity_data: Crawl activity data dict.
        proof_id: Pre-generated proof identifier.

    Returns:
        The Celery task ID (``UUID`` string), which can be used to poll
        task state from the result backend if needed.
    """
    store = get_store()

    # Initialize the proof record as pending
    store.set_status(proof_id, "pending", username=username)

    # Enqueue the task asynchronously
    task = generate_proof.delay(username, activity_data, proof_id)

    logger.info(
        "proof_enqueue: proof_id=%s username=%s celery_task_id=%s",
        proof_id,
        username,
        task.id,
    )

    return task.id
