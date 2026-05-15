---
estimated_steps: 10
estimated_files: 4
skills_used: []
---

# T01: Create attest/ module with Ed25519 key management, signing, and verification

Create the attestation module with three core functions:

1. `load_or_generate_signing_key(key_path=None)` — loads a private key from environment variable ATTEST_PRIVATE_KEY (base64) or auto-generates one (stored in-memory for the session). Returns (private_key, verify_key_bytes).

2. `sign_score(username, overall_score, signal_scores, risk_flags, profile_name, private_key)` — creates a canonical JSON payload of the score data, signs it with Ed25519, returns a dict with `signature` (base64), `public_key` (base64), `signed_payload` (JSON string), `signed_at` (ISO 8601 timestamp).

3. `verify_attestation(signed_payload, signature, public_key)` — verifies the Ed25519 signature. Returns `{ valid: bool, payload: dict }`.

Use PyNaCl's `nacl.signing.SigningKey` and `nacl.signing.VerifyKey` for Ed25519 operations. The canonical payload should be a deterministic JSON serialization (sorted keys) containing: username, overall_score, signal_scores (sorted by name), risk_flags (sorted), profile_name, signed_at.

Add `pynacl` to requirements.txt.

Module structure:
- `attest/__init__.py` — exports all public functions
- `attest/signer.py` — core signing and verification logic
- `attest/config.py` — key loading/management

## Inputs

- `requirements.txt`
- `scoring/engine.py`

## Expected Output

- `attest/__init__.py`
- `attest/signer.py`
- `attest/config.py`

## Verification

python -c "from attest import sign_score, verify_attestation, load_or_generate_signing_key; sk, vk = load_or_generate_signing_key(); sig = sign_score('testuser', 75.0, {'commit_consistency': {'score': 80, 'confidence': 0.8}}, [], 'engineering', sk); result = verify_attestation(sig['signed_payload'], sig['signature'], vk); assert result['valid']"
