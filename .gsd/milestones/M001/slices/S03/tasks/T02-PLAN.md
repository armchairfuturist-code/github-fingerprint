---
estimated_steps: 6
estimated_files: 2
skills_used: []
---

# T02: Wire attestation into ScoreResponse, /score, and /match endpoints

Update the FastAPI API layer to include attestation in all score responses:

1. Add an `attestation` field to `ScoreResponse` and `MatchResponse` Pydantic models: `Optional[Dict[str, Any]]` with fields `signature`, `public_key`, `signed_payload`, `signed_at`.

2. In both `/score` and `/match` endpoints, after computing the score, call `attest.sign_scores(...)` to produce the attestation block. Add it to the response.

3. Handle the case where the signing key is unavailable (log warning, omit attestation block from response — don't crash).

4. Initialize the attestation module at module level in `api/main.py`: call `load_or_generate_signing_key()` during startup, and pass the verify key bytes or private key to the signing function.

5. Export the verify_key_bytes so the /verify endpoint can use them.

## Inputs

- `api/main.py`
- `attest/__init__.py`
- `attest/signer.py`
- `attest/config.py`

## Expected Output

- `api/main.py`

## Verification

grep -q "attestation" api/main.py
