---
id: T03
parent: S03
milestone: M002
key_files:
  - api/main.py
  - tests/test_api.py
key_decisions:
  - Proof status endpoint uses existing ProofStatusStore singleton to avoid duplicating state
  - ProofStatusResponse includes attestation for full-picture view as required by task plan
duration: 
verification_result: passed
completed_at: 2026-05-12T09:06:19.027Z
blocker_discovered: false
---

# T03: Added GET /proof/{username}/status endpoint with full proof lifecycle tracking (pending→proof_generating→proof_generated→on_chain→failed) plus Ed25519 attestation

**Added GET /proof/{username}/status endpoint with full proof lifecycle tracking (pending→proof_generating→proof_generated→on_chain→failed) plus Ed25519 attestation**

## What Happened

Added the proof status tracking endpoint GET /proof/{username}/status to api/main.py. The endpoint uses the existing in-memory ProofStatusStore singleton (from T02) to query proof lifecycle state by username. It returns the proof status, timing info (created_at/updated_at), optional proof_path/tx_hash/error, and an Ed25519 attestation block when the signing key is available. Added a ProofStatusResponse Pydantic model for typed responses. When no proof record exists, returns status 'unknown' with an attestation block if available. Added 8 new tests covering: endpoint registration, unknown user, post-score integration, response shape, all status transitions (pending→proof_generating→proof_generated→on_chain→failed), attestation inclusion, multi-user isolation, and JSON content-type. All 264 tests pass.

## Verification

Full test suite passes: python -m pytest tests/ → 264 passed in 1.02s. Endpoint returns correct status for all lifecycle transitions. Attestation block included in response. Multi-user isolation works correctly.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/` | 0 | ✅ pass | 1020ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/main.py`
- `tests/test_api.py`
