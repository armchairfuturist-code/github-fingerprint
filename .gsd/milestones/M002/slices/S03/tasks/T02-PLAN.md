---
estimated_steps: 10
estimated_files: 3
skills_used: []
---

# T02: Celery/Redis async queue for proof generation

Set up Celery with Redis broker:
- Requirements: celery[redis] in requirements.txt
- Create celery_app in api/ with Redis config
- Create proof generation task: @celery.task that calls run_proof() from prover_client
- Configure task routing, retries (3 retries, exponential backoff)
- Worker startup script

Wire proof generation into the score flow:
- After /score returns, enqueue proof generation task
- Task creates the proof and stores status in a DB/memory store

Output: Celery worker starts, picks up proof tasks, generates proofs successfully.

## Inputs

- `api/prover_client.py (from S02 T03)`
- `api/main.py`

## Expected Output

- `api/celery_app.py`
- `api/proof_tasks.py`
- `api/worker.py (startup script)`

## Verification

celery -A api.celery_app worker starts. Post /score → Celery task enqueued. Task generates proof. Failed tasks retry with backoff.
