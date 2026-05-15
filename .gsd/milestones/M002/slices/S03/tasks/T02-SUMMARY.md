---
id: T02
parent: S03
milestone: M002
key_files:
  - api/celery_app.py
  - api/proof_tasks.py
  - api/proof_status.py
  - api/worker.py
  - api/main.py
  - requirements.txt
  - tests/conftest.py
  - tests/test_celery.py
  - tests/test_proof_status.py
  - tests/test_proof_tasks.py
key_decisions:
  - Use Celery with Redis for async proof generation instead of FastAPI BackgroundTasks
  - Thread-safe in-memory ProofStatusStore for tracking proof lifecycle, upgradable to Redis/DB later
  - Ed25519 attestation always returned immediately — Celery/Redis failure never blocks the score response
  - 3 retries with exponential backoff (max 10min) and jitter for task reliability
  - acs_late + reject_on_worker_lost for at-least-once delivery semantics
  - Conftest auto-mocking of enqueue_proof to prevent test hangs without Redis
duration: 
verification_result: passed
completed_at: 2026-05-12T09:04:02.676Z
blocker_discovered: false
---

# T02: Set up Celery/Redis async queue for proof generation with retry and status tracking; wired Celery enqueue into /score endpoint with Ed25519 fallback preserved.

**Set up Celery/Redis async queue for proof generation with retry and status tracking; wired Celery enqueue into /score endpoint with Ed25519 fallback preserved.**

## What Happened

Created the full Celery/Redis async queue infrastructure for proof generation:

1. **api/celery_app.py** — Celery app configured with Redis broker/backend, `proof_generation` queue, acks_late delivery, JSON serialization, and UTC timezone.

2. **api/proof_tasks.py** — `generate_proof` Celery task with 3 retries (exponential backoff, max 10min, jitter). Task calls `run_proof()` from prover_client and updates the ProofStatusStore through lifecycle (pending → proof_generating → proof_generated/failed). Public `enqueue_proof()` helper initializes status and dispatches the task.

3. **api/proof_status.py** — Thread-safe in-memory `ProofStatusStore` with get/set/list/count-by-status operations. Stores proof_id, username, status, timestamps, proof_path, tx_hash, error, and metadata. Module-level singleton for cross-module sharing.

4. **api/worker.py** — Worker startup script with configurable log level, concurrency, and queue.

5. **Wire into api/main.py** — Replaced FastAPI BackgroundTasks-based proof generation with Celery `enqueue_proof()` in the `/score` endpoint. Ed25519 attestation fallback preserved: if Celery/Redis is unavailable, the error is logged and the score response still returns immediately with attestation.

6. **test conftest.py** — Auto-mocking fixture for enqueue_proof prevents test hangs (Redis not required for unit tests).

7. **tests/test_celery.py** — 7 tests verifying celery app config, default queue, serialization, Redis URL, and env var override.

8. **tests/test_proof_status.py** — 20 tests covering full lifecycle, thread safety, singleton pattern, filtering, counting, and edge cases.

9. **tests/test_proof_tasks.py** — 10 tests covering enqueue helper, task status transitions (pending→generating→generated/failed), retry config, exception handling, and task metadata.

10. **requirements.txt** — Updated: celery[redis]==5.6.3, redis==6.4.0.

## Verification

All 256 tests pass. Module imports verify correctly: celery_app loads with correct config (task_default_queue=proof_generation, acks_late=True). generate_proof task has name=generate_proof, max_retries=3, retry_backoff=True. ProofStatusStore lifecycle verified (pending→proof_generating→proof_generated with proof_path). enqueue_proof dispatches correctly with mock. /score endpoint returns 200 with attestation and proof_id even when Redis is unavailable (verified via test suite).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/` | 0 | ✅ pass | 940ms |
| 2 | `python -c 'verify imports and config'` | 0 | ✅ pass | 500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/celery_app.py`
- `api/proof_tasks.py`
- `api/proof_status.py`
- `api/worker.py`
- `api/main.py`
- `requirements.txt`
- `tests/conftest.py`
- `tests/test_celery.py`
- `tests/test_proof_status.py`
- `tests/test_proof_tasks.py`
