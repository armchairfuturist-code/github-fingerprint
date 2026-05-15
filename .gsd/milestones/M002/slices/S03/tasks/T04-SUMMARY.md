---
id: T04
parent: S03
milestone: M002
key_files:
  - tests/test_proving_e2e.py
  - docs/failure-modes.md
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-12T09:09:56.901Z
blocker_discovered: false
---

# T04: Created E2E integration smoke test (22 tests) and failure mode documentation covering Celery/Redis down, prover network failure, missing GITHUB_TOKEN, proof lifecycle transitions, and Ed25519 attestation fallback.

**Created E2E integration smoke test (22 tests) and failure mode documentation covering Celery/Redis down, prover network failure, missing GITHUB_TOKEN, proof lifecycle transitions, and Ed25519 attestation fallback.**

## What Happened

Created tests/test_proving_e2e.py with 22 tests organized into 9 test classes covering: attestation return on /score, attestation verifiability, Ed25519 fallback when Celery/Redis is down (enqueue_proof raises), proof status lifecycle transitions (pending → proof_generating → proof_generated → on_chain → failed), Celery task failure modes (missing CLI binary, network timeout, invalid proof), multiple user isolation, full attestation round-trip, queue depth gauge (count_by_status), prover network down scenarios, and missing GITHUB_TOKEN handling. Also created docs/failure-modes.md documenting 10 failure modes with impact, detection, recovery, and test coverage references. All 286 tests pass (264 original + 22 new).

## Verification

All 22 new E2E tests pass. Full test suite (286 tests) passes. Verified: Ed25519 attestation returned even with Celery/Redis unavailable (enqueue_proof raises). Proof status correctly shows 'failed' when prover fails. Proof status lifecycle transitions verified end-to-end. Smoke test script exits 0.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_proving_e2e.py -v` | 0 | ✅ pass | 260ms |
| 2 | `python -m pytest tests/ -v` | 0 | ✅ pass | 1000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_proving_e2e.py`
- `docs/failure-modes.md`
