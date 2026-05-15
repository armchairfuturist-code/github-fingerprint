---
id: T02
parent: S04
milestone: M003
key_files:
  - api/main.py
  - templates/profile.html
key_decisions:
  - proof_path surfaced from ProofStatusStore top-level record field
  - verifying_contract extracted from metadata sub-dict — future-proofed for when contract address is stored during proving pipeline update
duration: 
verification_result: passed
completed_at: 2026-05-15T05:43:23.799Z
blocker_discovered: false
---

# T02: Added proof_path and verifying_contract fields to the profile route and expandable proof viewer template

**Added proof_path and verifying_contract fields to the profile route and expandable proof viewer template**

## What Happened

Updated the proof_status_data construction in the profile route (api/main.py) to include two new fields: (1) proof_path from the ProofStatusStore top-level field, and (2) verifying_contract extracted from the metadata sub-dict. Then added conditional template rows for both fields in the expandable proof viewer (templates/profile.html), positioned between Tx Hash and Error rows. Both fields are conditionally shown only when populated, matching the existing pattern.

## Verification

pytest tests/test_api.py::TestProofStatusEndpoint -q returns 8 passed. pytest tests/test_api.py -q -k "profile" returns 8 passed. pytest -q --tb=short --ignore=smoke_test.py returns 372 passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_api.py::TestProofStatusEndpoint -q --tb=short` | 0 | ✅ pass — 8/8 proof status endpoint tests pass | 300ms |
| 2 | `pytest -q --tb=short --ignore=smoke_test.py` | 0 | ✅ pass — 372 tests pass | 1920ms |

## Deviations

None.

## Known Issues

The verifying_contract field will only render when the proving pipeline stores it in metadata. Currently the Celery proof task (proof_tasks.py: set_status call for proof_generated) stores proving_time_ms, proving_time_seconds, prover, and input_summary in metadata — but not verifying_contract yet. The template row will appear automatically once the contract address is added to metadata.

## Files Created/Modified

- `api/main.py`
- `templates/profile.html`
