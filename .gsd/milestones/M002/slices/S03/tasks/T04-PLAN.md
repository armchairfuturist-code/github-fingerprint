---
estimated_steps: 7
estimated_files: 2
skills_used: []
---

# T04: End-to-end integration test and failure mode documentation

End-to-end verification:
- Run the full flow: /score → Ed25519 attestation returned → proof enqueued → proof generated → proof submitted on-chain
- Verify proof on Base Sepolia explorer
- Test Ed25519 fallback: what happens when Celery/Redis is down? Score still returns with Ed25519 attestation, proof status = pending/failed
- Test failure modes: bad GITHUB_TOKEN, prover network down, Redis down, invalid proof
- Write a smoke test script that exercises the full flow

Output: E2E smoke test passes. Edge cases documented.

## Inputs

- `api/main.py`
- `api/celery_app.py`
- `api/proof_status.py`
- `api/prover_client.py`

## Expected Output

- `tests/test_proving_e2e.py`
- `docs/failure-modes.md`

## Verification

Smoke test script exits 0. Ed25519 attestation returned even with Celery/Redis unavailable. Proof status correctly shows 'failed' when prover network is down.
