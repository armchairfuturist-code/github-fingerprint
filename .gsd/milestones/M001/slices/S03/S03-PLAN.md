# S03: Attestation Upgrade

**Goal:** Every score response includes an independently verifiable Ed25519 signature covering the overall score and all signal scores, and a /verify endpoint allows third parties to verify authenticity of attested scores.
**Demo:** Every score carries an independently verifiable Ed25519 signature covering all signals.

## Must-Haves

- /score and /match responses include `attestation` block with `signature` (base64), `public_key` (base64), `signed_payload` (serialized canonical payload), and `signed_at` (ISO timestamp)
- A tampered payload fails verification
- A valid signature verifies successfully via both the attest module API and the /verify endpoint
- /verify endpoint returns `{ valid: true/false, payload: ... }` for valid/invalid signatures
- Attestation gracefully degrades when no signing key is configured (response omits attestation block)
- All tests pass: signing correctness, verification, tamper detection, API integration, missing-key handling

## Proof Level

- This slice proves: This slice proves contract and integration: the attestation module signs and verifies correctly at the unit level, the API endpoints produce attestable responses at the HTTP contract level, and the /verify endpoint closes the verification loop.

## Integration Closure

Upstream surfaces consumed: ScoreResult from scoring/engine.py, FastAPI app from api/main.py, ProfileResponse/ScoreResponse/MatchResponse Pydantic models from api/main.py. New wiring introduced: attest/ module integrated into /score and /match as a post-scoring step, new /verify endpoint registered. What remains before milestone is usable end-to-end: S04 (Integration & Polish) wires the full end-to-end flow with frontend display of attestation status and incremental updates.

## Verification

- Runtime signals: attest.sign_scores logs each signing event (username, timestamp, signature prefix). If signing key is missing or invalid, attestation is gracefully omitted from responses with a log warning. Inspection surfaces: /verify endpoint serves as the canonical verification surface. Failure visibility: missing or invalid key shows as omitted attestation block in /score and /match responses, + warning log entry.

## Tasks

- [x] **T01: Create attest/ module with Ed25519 key management, signing, and verification** `est:1h`
  Create the attestation module with three core functions:
  - Files: `attest/__init__.py`, `attest/signer.py`, `attest/config.py`, `requirements.txt`
  - Verify: python -c "from attest import sign_score, verify_attestation, load_or_generate_signing_key; sk, vk = load_or_generate_signing_key(); sig = sign_score('testuser', 75.0, {'commit_consistency': {'score': 80, 'confidence': 0.8}}, [], 'engineering', sk); result = verify_attestation(sig['signed_payload'], sig['signature'], vk); assert result['valid']"

- [x] **T02: Wire attestation into ScoreResponse, /score, and /match endpoints** `est:1h`
  Update the FastAPI API layer to include attestation in all score responses:
  - Files: `api/main.py`, `attest/__init__.py`
  - Verify: grep -q "attestation" api/main.py

- [x] **T03: Add /verify endpoint for signature verification** `est:30m`
  Add a POST /verify endpoint that accepts a verification request payload:
  - Files: `api/main.py`, `attest/__init__.py`, `attest/signer.py`
  - Verify: grep -q "verify" api/main.py && grep -q "/verify" api/main.py

- [x] **T04: Add comprehensive tests for attestation module and API integration** `est:1h`
  Add test files for the attestation module:
  - Files: `tests/test_attest.py`, `tests/test_api.py`, `attest/__init__.py`, `attest/signer.py`
  - Verify: python -m pytest tests/test_attest.py tests/test_api.py -v --tb=short

## Files Likely Touched

- attest/__init__.py
- attest/signer.py
- attest/config.py
- requirements.txt
- api/main.py
- tests/test_attest.py
- tests/test_api.py
