---
id: T03
parent: S03
milestone: M001
key_files:
  - api/main.py
  - tests/test_api.py
key_decisions:
  - /verify endpoint delegates to attest.verify_attestation() directly for thin verification surface
  - VerifyRequest uses three str fields (signed_payload, signature, public_key) matching the sign_score output shape
  - Error responses use FastAPI 422 for missing fields (Pydantic built-in) and 200 with valid:false + error for logic failures
duration: 
verification_result: passed
completed_at: 2026-05-12T06:15:44.356Z
blocker_discovered: false
---

# T03: Added POST /verify endpoint that accepts signed_payload, signature, and public_key; returns valid bool, parsed payload, and optional error; with 9 new tests covering valid, tampered, missing-field, and empty-input cases.

**Added POST /verify endpoint that accepts signed_payload, signature, and public_key; returns valid bool, parsed payload, and optional error; with 9 new tests covering valid, tampered, missing-field, and empty-input cases.**

## What Happened

Added the POST /verify endpoint to api/main.py. The implementation: (1) imported verify_attestation from the attest module, (2) added VerifyRequest and VerifyResponse Pydantic models, (3) registered the @app.post('/verify') endpoint that delegates to attest.verify_attestation(). Malformed inputs are handled by FastAPI's built-in 422 validation for missing fields, while the underlying attest.verify_attestation() handles invalid base64/bad signatures gracefully (returns valid: false with error message). Also added 9 tests: 3 model tests for VerifyRequest/VerifyResponse, 1 route registration test, and 5 functional TestClient tests covering valid signatures, tampered payloads, missing fields (422), and empty strings (200 with valid: false).

## Verification

All 156 tests pass (was 147, added 9). grep confirms 'verify' and '/verify' are present in api/main.py. End-to-end manual verification: generated a signing key, signed a score payload, verified via verify_attestation() — valid=True with correct payload fields.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/ -v` | 0 | ✅ pass — 156 passed | 230ms |
| 2 | `grep -q 'verify' api/main.py && grep -q '/verify' api/main.py` | 0 | ✅ pass — both strings found | 50ms |
| 3 | `python -c '...sign + verify_attestation end-to-end...'` | 0 | ✅ pass — valid=True, payload correct | 100ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/main.py`
- `tests/test_api.py`
