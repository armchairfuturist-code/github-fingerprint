# Failure Modes: ZK Proving & Scoring Pipeline

This document catalogs known failure modes in the GitHub Fingerprint scoring
pipeline, covering the ZK proof generation subsystem (Celery/Redis/SP1 prover),
attestation, and the API surface.

---

## Table of Contents

1. [Celery/Redis Unavailable](#1-celeryredis-unavailable)
2. [Prover CLI Binary Missing](#2-prover-cli-binary-missing)
3. [Prover Network Timeout](#3-prover-network-timeout)
4. [Invalid SP1 Proof](#4-invalid-sp1-proof)
5. [Invalid / Missing GITHUB_TOKEN](#5-invalid--missing-github_token)
6. [Proof Task Exception After Retries](#6-proof-task-exception-after-retries)
7. [Proof Status Store Contention](#7-proof-status-store-contention)
8. [Attestation Key Unavailable](#8-attestation-key-unavailable)
9. [Score Data Malformed](#9-score-data-malformed)
10. [Base Sepolia RPC Unreachable](#10-base-sepolia-rpc-unreachable)

---

## 1. Celery/Redis Unavailable

### Impact

- **Score endpoint** (`POST /score`): **No impact**. The Ed25519 attestation
  and score are computed and returned immediately. The failed `enqueue_proof()`
  call is caught by a `try/except` in the endpoint handler, which logs the
  error and continues.
- **Proof status** (`GET /proof/{username}/status`): Returns `"unknown"` because
  `enqueue_proof` never set an initial status in the `ProofStatusStore`.
- **Proving pipeline**: No proof is generated.

### Detection

- Logs show `proof_enqueue_failed: proof_id=... — Ed25519 attestation still
  returned, Celery/Redis may be down` at WARNING level.
- Celery worker heartbeat monitoring returns no live workers.

### Recovery

1. Start Redis: `redis-server`
2. Start Celery worker: `celery -A api.celery_app worker --loglevel=info`
3. Existing score results that missed proof generation can be re-enqueued
   manually, or the user can submit a new score request.

### Test Coverage

- `tests/test_proving_e2e.py::TestEd25519Fallback`
- `tests/test_proving_e2e.py::TestProverNetworkDown`

---

## 2. Prover CLI Binary Missing

### Impact

- **Score endpoint**: No impact — `run_proof()` is called asynchronously in
  the Celery worker, not in the request handler.
- **Celery task**: The `generate_proof` task raises `FileNotFoundError` when
  `scoring-prover-cli` is not found. The task is configured with 3 retries
  with exponential backoff (max 10 minutes). After exhausting retries, Celery
  stores the task as FAILED.
- **Proof status**: The `ProofStatusStore` is updated to `"failed"` with
  `error` containing the `FileNotFoundError` message.

### Detection

- Celery worker logs show `FileNotFoundError` — binary not found.
- Celery flower or `celery inspect` shows failed tasks.

### Recovery

1. Install (or build) the `scoring-prover-cli` binary.
2. Set `SCORING_PROVER_CLI` env var to the binary path if it's not on PATH.
3. Clear the failed task or re-run scoring.

### Test Coverage

- `tests/test_proving_e2e.py::TestCeleryTaskFailureModes::test_prover_cli_missing_is_handled`
- `tests/test_prover_client.py`

---

## 3. Prover Network Timeout

### Impact

- **Score endpoint**: No impact — proof generation is asynchronous.
- **Celery task**: `subprocess.TimeoutExpired` is raised if the CLI does not
  finish within 600 seconds (10 minutes). The task retries with exponential
  backoff.
- **Proof status**: After 3 failed retries, status is set to `"failed"`.

### Detection

- Celery worker logs show `run_proof: proof_id=... timed out after 600s`.
- `ProofStatusStore` shows `failed` with `error: "TimeoutExpired: ..."`.

### Recovery

1. Check the SP1 prover network status.
2. Increase the timeout via the `timeout` parameter to `run_proof()`.
3. Re-enqueue the proof (e.g., via a retry endpoint or by re-scoring the user).

### Test Coverage

- `tests/test_proving_e2e.py::TestCeleryTaskFailureModes::test_retry_on_network_error`
- `tests/test_proof_tasks.py`

---

## 4. Invalid SP1 Proof

### Impact

- **Score endpoint**: No impact.
- **Celery task**: The prover CLI returns a non-zero exit code. The task
  captures stderr as the error and sets proof status to `"failed"`.
- **Proof status**: Shows `"failed"` with the CLI error message.

### Possible Causes

- Mismatched SP1 version between the scoring circuit and the verifier contract.
- Corrupted input data.
- Constraint system violation in the SP1 circuit.
- Scoring data that does not match the expected input schema.

### Detection

- Celery logs show `proof_task: proof_id=... FAILED (CLI): <error>`.
- `ProofStatusStore.get_status()` returns `"failed"` with error detail.

### Recovery

1. Check SP1 version compatibility.
2. Validate input data schema.
3. If the input schema changed, regenerate the proving circuit.
4. Re-run the score with corrected data.

### Test Coverage

- `tests/test_proving_e2e.py::TestCeleryTaskFailureModes::test_failed_proof_sets_failed_status`
- `tests/test_proof_tasks.py::TestGenerateProofTask::test_task_handles_cli_failure`

---

## 5. Invalid / Missing GITHUB_TOKEN

### Impact

- **Score endpoint**: Returns **500 Internal Server Error** with detail
  `"GITHUB_TOKEN environment variable is required"` or `"Error scoring user"`.
- **All crawling**: Fails because the GitHub API client cannot initialize.
- **Other endpoints** (`/match`, scoring): Also fail if they need a token.

### Detection

- API response shows 500 with `detail` containing `"GITHUB_TOKEN"`.
- Server logs show `ValueError: GITHUB_TOKEN environment variable is required`.

### Recovery

1. Set `GITHUB_TOKEN` environment variable with a valid GitHub personal access
   token.
2. Restart the API server.
3. Re-submit the request.

### Test Coverage

- `tests/test_proving_e2e.py::TestInvalidGitHubToken`
- `tests/test_api.py` (error handling)

---

## 6. Proof Task Exception After Retries

### Impact

- **Celery task**: After exhausting 3 retries with exponential backoff, the task
  is permanently marked as FAILED.
- **Proof status**: Status is set to `"failed"` with the error message from the
  last exception.
- **No on-chain verification**: The Groth16 proof is never submitted.

### Retry Configuration

| Parameter        | Value    |
|-----------------|----------|
| `max_retries`    | 3        |
| `retry_backoff`  | True     |
| `retry_backoff_max` | 600s (10 min) |
| `retry_jitter`   | True     |
| `acks_late`      | True     |

### Detection

- `ProofStatusStore.count_by_status()` shows accumulated `"failed"` records.
- Celery worker logs show `proof_task: proof_id=... EXCEPTION attempt=3/4: ...`
  followed by task failure event.

### Recovery

1. Inspect the error message from `GET /proof/{username}/status`.
2. Fix the underlying issue (see other failure modes).
3. Re-score the user to trigger a new proof generation attempt.

### Test Coverage

- `tests/test_proof_tasks.py::TestGenerateProofTask::test_task_retries_on_exception`
- `tests/test_proving_e2e.py::TestCeleryTaskFailureModes::test_retry_on_network_error`

---

## 7. Proof Status Store Contention

### Impact

- **Concurrent score requests**: Multiple requests for the same username create
  multiple proof records with different `proof_id` values.
- **`get_status_by_username`**: Returns the **most recently updated** record,
  which may not be the desired one. This is intentional — the latest attempt
  is usually the most relevant.
- **No data corruption**: The `threading.Lock` in `ProofStatusStore` prevents
  race conditions on concurrent writes.

### Mitigation

- The store is thread-safe. For production, a Redis-backed or SQL-backed store
  should be swapped in, providing atomic per-user status updates and
  horizontal scaling.

### Detection

- Multiple proof records for the same username with different `proof_id` values
  (visible via `list_statuses()` or introspection).

### Test Coverage

- `tests/test_proof_status.py::TestProofStatusStore::test_thread_safety`
- `tests/test_proof_status.py::TestProofStatusStore::test_get_status_by_username`

---

## 8. Attestation Key Unavailable

### Impact

- **Score/Verification endpoints**: The `attestation` field in API responses
  is `null` when the Ed25519 signing key cannot be initialized.
- **Attestation verification**: Fails with `valid: false` and an error message.
- **No crash**: The endpoints log a warning and continue, returning the score
  without attestation.

### Possible Causes

- `SIGNING_KEY_FILE` environment variable points to a non-existent or
  unreadable file.
- File-based key generation fails (permission, disk full).
- NaCL library malfunction.

### Detection

- Logs show `Failed to initialize attestation signing key. Attestation will be omitted.`
- API responses show `"attestation": null`.

### Recovery

1. Ensure NaCL (`PyNaCl`/`nacl` dependency) is installed.
2. Set `SIGNING_KEY_FILE` to a writable path or remove it to let the system
   auto-generate a key.
3. Restart the API server.

### Test Coverage

- `attest` module test suite (`tests/test_attest.py`)
- Existing API tests verify attestation shape.

---

## 9. Score Data Malformed

### Impact

- **Score endpoint**: Returns **400 Bad Request** with descriptive error if
  the scoring engine rejects the input, or **500 Internal Server Error** for
  unexpected failures.
- **Proof generation**: The Celery task may fail if the activity data is
  missing expected keys. `run_proof()` handles missing keys gracefully
  (defaulting to empty lists), but malformed nested data could still cause
  errors.

### Possible Causes

- GitHub API returns unexpectedly shaped data (rate limiting, schema changes).
- Missing keys in the activity data dict that the scoring engine expects.

### Detection

- API responses show 400/500 with descriptive error messages.
- Server logs show traceback with the specific malformed data.

### Recovery

1. Check GitHub API status and token permissions.
2. Re-submit the request after the transient issue resolves.
3. If the error persists, the input schema may have changed — check
   `GitHubAPIClient` return values and the `ScoringEngine` input format.

### Test Coverage

- Scoring engine edge-case tests.
- API error handling tests (`test_integration.py::TestErrorHandling`).

---

## 10. Base Sepolia RPC Unreachable

### Impact

- **On-chain verification**: Proofs cannot be submitted on-chain.
- **Proof status**: If the on-chain submission step is automated, the status
  would remain at `"proof_generated"` and never transition to `"on_chain"`.
- **Score endpoint**: No impact — on-chain submission is a separate step.

### Detection

- Proofs accumulate at `"proof_generated"` status without transitioning to
  `"on_chain"`.
- Contract interaction logs show RPC connection errors.

### Recovery

1. Check Base Sepolia RPC endpoint availability (e.g., Alchemy, Infura status).
2. Retry the on-chain submission when the RPC is available.
3. The Explorer link for the verifier contract can be checked independently:
   `https://sepolia.basescan.org/address/<verifier_address>`

### Test Coverage

- Contract-based tests in `tests/test_verifier_contract.cjs` (Hardhat/Forge).
- On-chain submission is a manual step in the current iteration.

---

## Observability Surfaces

| Surface | Location | Purpose |
|---------|----------|---------|
| Proof status store count | `ProofStatusStore.count_by_status()` | Queue depth gauge |
| Proof status transitions | Log: `proof_store: proof_id=... status=...` | Track lifecycle |
| Proof enqueue events | Log: `proof_enqueue: proof_id=...` | Track enqueue success |
| Proof enqueue failures | Log: `proof_enqueue_failed: proof_id=...` | Detect Celery/Redis down |
| Proof task completion | Log: `proof_task: proof_id=... COMPLETED` | Track proof success |
| Proof task failures | Log: `proof_task: proof_id=... FAILED` | Track proof failures |
| Proof task exceptions | Log: `proof_task: proof_id=... EXCEPTION` | Track transient errors |
| Celery worker heartbeat | `celery -A api.celery_app inspect ping` | Worker liveness |
| Attestation events | Log: `Attested score for user=...` | Track attestation generation |
| Attestation failures | Log: `Signing key not available` | Detect missing key config |

## Queue Depth Gauge

The `ProofStatusStore.count_by_status()` method provides real-time visibility
into the proof queue depth. In production, this should be exposed as a
Prometheus metric or health check endpoint:

```python
from api.proof_status import get_store

gauges = get_store().count_by_status()
# => {"pending": 3, "proof_generating": 2, "proof_generated": 5,
#     "failed": 1}
```

A large `pending` count may indicate that Celery workers are not keeping up.
A growing `failed` count indicates an underlying issue requiring investigation.
