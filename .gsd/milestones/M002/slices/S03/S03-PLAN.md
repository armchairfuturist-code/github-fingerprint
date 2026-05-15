# S03: Base Verifier Contract & API Integration

**Goal:** Deploy the SP1 Groth16 verifier contract on Base, wire Celery/Redis async proving queue into the API, add proof status polling endpoint, and preserve Ed25519 fallback.
**Demo:** POST /score returns immediately with Ed25519 attestation; proof status endpoint shows in-progress → on_chain

## Must-Haves

- Solidity verifier contract deployed on Base Sepolia
- Celery/Redis async queue picks up proof generation jobs
- GET /proof/{username}/status endpoint returns: pending | proof_generating | on_chain | failed
- Ed25519 fallback preserved — ZK proving failure never blocks scores
- Proof status indicator in frontend (optional, can be M003)

## Proof Level

- This slice proves: Full — contract deployed on testnet, proof status pollable via API, Ed25519 scores returned without blocking on proof

## Integration Closure

Closes the ZK proving loop: score → async prove → on-chain verify. The API returns both instant Ed25519 attestation and async ZK proof status. The Celery queue handles retries and failures gracefully.

## Verification

- Queue depth gauge, proof status transitions logged, verification events logged, Celery worker heartbeat. Failed jobs tracked with retry count and last error.

## Tasks

- [x] **T01: Deploy SP1 verifier contract on Base Sepolia** `est:1.5h`
  Use SP1's Solidity verifier template:
  - Run `cargo prove deploy` or SP1's forge template to generate verifier contract
  - Deploy to Base Sepolia testnet
  - Verify contract on Base Sepolia explorer
  - Save deployed contract address and ABI
  - Files: `contracts/SP1Verifier.sol`, `contracts/deployed-address.txt`, `contracts/abi/SP1Verifier.json`
  - Verify: Contract verified on Base Sepolia explorer. Test: submit a known-valid Groth16 proof → verification passes. Test: submit invalid proof → verification fails.

- [x] **T02: Celery/Redis async queue for proof generation** `est:1.5h`
  Set up Celery with Redis broker:
  - Requirements: celery[redis] in requirements.txt
  - Create celery_app in api/ with Redis config
  - Create proof generation task: @celery.task that calls run_proof() from prover_client
  - Configure task routing, retries (3 retries, exponential backoff)
  - Worker startup script
  - Files: `api/celery_app.py`, `api/proof_tasks.py`, `requirements.txt`
  - Verify: celery -A api.celery_app worker starts. Post /score → Celery task enqueued. Task generates proof. Failed tasks retry with backoff.

- [x] **T03: Proof status tracking and API endpoint** `est:1h`
  Add proof status tracking and API endpoint:
  - Simple ProofStatus store: dict or SQLite (upgradable to PostgreSQL later)
    - proof_id: str
    - username: str
    - status: pending | proof_generating | proof_generated | on_chain | failed
    - created_at, updated_at
    - proof_path (nullable)
    - tx_hash (nullable, when submitted on-chain)
    - error (nullable)
  - GET /proof/{username}/status returns current proof status
  - Auto-submit proof on-chain after generation (optional — can be manual step for now)
  - Endpoint returns Ed25519 attestation alongside proof status for full picture
  - Files: `api/proof_status.py`, `api/main.py`
  - Verify: POST /score with username 'testuser' → status is 'proof_generating'. Wait for Celery task → status becomes 'proof_generated' or 'on_chain'. GET /proof/testuser/status returns correct status. Ed25519 attestation always returned regardless of proof status.

- [x] **T04: End-to-end integration test and failure mode documentation** `est:1h`
  End-to-end verification:
  - Run the full flow: /score → Ed25519 attestation returned → proof enqueued → proof generated → proof submitted on-chain
  - Verify proof on Base Sepolia explorer
  - Test Ed25519 fallback: what happens when Celery/Redis is down? Score still returns with Ed25519 attestation, proof status = pending/failed
  - Test failure modes: bad GITHUB_TOKEN, prover network down, Redis down, invalid proof
  - Write a smoke test script that exercises the full flow
  - Files: `tests/test_proving_e2e.py`, `docs/failure-modes.md`
  - Verify: Smoke test script exits 0. Ed25519 attestation returned even with Celery/Redis unavailable. Proof status correctly shows 'failed' when prover network is down.

## Files Likely Touched

- contracts/SP1Verifier.sol
- contracts/deployed-address.txt
- contracts/abi/SP1Verifier.json
- api/celery_app.py
- api/proof_tasks.py
- requirements.txt
- api/proof_status.py
- api/main.py
- tests/test_proving_e2e.py
- docs/failure-modes.md
