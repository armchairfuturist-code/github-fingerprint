---
estimated_steps: 17
estimated_files: 4
skills_used: []
---

# T04: Add comprehensive tests for attestation module and API integration

Add test files for the attestation module:

1. `tests/test_attest.py` — Test the attest module directly:
   - sign_score produces non-empty signature, public_key, signed_payload, signed_at
   - verify_attestation returns valid=True for a correctly signed payload
   - verify_attestation returns valid=False for tampered payload (modify one byte)
   - verify_attestation returns valid=False for wrong public key
   - verify_attestation handles malformed inputs (empty strings, invalid base64, truncated data)
   - load_or_generate_signing_key produces valid Ed25519 key pair
   - Canonical payload sorting ensures deterministic signing

2. Add tests to `tests/test_api.py` for attestation wiring:
   - /score response includes attestation block
   - /match response includes attestation block
   - /verify POST endpoint accepts valid signature and returns valid=True
   - /verify POST rejects tampered payload
   - /verify POST returns 400 for malformed input
   - Attestation is consistent: same score produces same signed_payload

3. Run the full test suite to ensure no regressions.

## Inputs

- `tests/test_api.py`
- `attest/__init__.py`
- `attest/signer.py`
- `api/main.py`

## Expected Output

- `tests/test_attest.py`

## Verification

python -m pytest tests/test_attest.py tests/test_api.py -v --tb=short
