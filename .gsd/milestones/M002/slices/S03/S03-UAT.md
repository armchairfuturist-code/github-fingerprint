# S03: Base Verifier Contract & API Integration — UAT

**Milestone:** M002
**Written:** 2026-05-12T09:12:51.031Z

# UAT: S03 — Base Verifier Contract & API Integration

## Preconditions
- Python 3.11+ with dependencies installed (`pip install -r requirements.txt`)
- GITHUB_TOKEN environment variable set (valid GitHub PAT)
- Redis running on localhost:6379 (optional — Ed25519 fallback works without it)
- Celery worker available (optional for testing with mocked proving)

## Test Scenarios

### TC01: POST /score returns Ed25519 attestation immediately
1. Send `POST /score` with `{"username": "testuser"}`
2. **Expected:** HTTP 200 with `attestation` block containing `signature`, `public_key`, `signed_payload`, and `signed_at`
3. **Expected:** `proof_id` is present in response
4. **Expected:** `overall_score` and `signal_scores` are populated

### TC02: Attestation is verifiable via /verify
1. Send `POST /score` for any username
2. Extract `attestation` from response
3. Send `POST /verify` with `signed_payload`, `signature`, and `public_key` from attestation
4. **Expected:** HTTP 200 with `{"valid": true, "payload": {...}}`
5. Tamper with the signature — send invalid signature
6. **Expected:** HTTP 200 with `{"valid": false}`
7. Send verify request with missing fields
8. **Expected:** HTTP 422

### TC03: Ed25519 fallback — score works when Celery/Redis is down
1. Stop Redis (or simulate enqueue failure)
2. Send `POST /score` with `{"username": "fallback_user"}`
3. **Expected:** HTTP 200 with `attestation` present
4. **Expected:** `overall_score` is populated normally
5. **Expected:** No server error — proof enqueue failure does not propagate to caller

### TC04: GET /proof/{username}/status — lifecycle transitions
1. Send `POST /score` for a user (e.g., "lifecycle_user")
2. Get `proof_id` from response
3. GET `/proof/lifecycle_user/status` — confirm status is `pending`
4. Manually drive status through: `proof_generating`, `proof_generated`, `on_chain`, `failed`
5. **Expected:** Each GET returns the correct status with timestamps
6. **Expected:** `proof_generated` status includes `proof_path`
7. **Expected:** `on_chain` status includes `tx_hash`
8. **Expected:** `failed` status includes `error` message

### TC05: GET /proof/{username}/status — unknown user
1. GET `/proof/nonexistent_user/status`
2. **Expected:** HTTP 200 with `{"status": "unknown"}`

### TC06: GET /proof/{username}/status — includes attestation
1. After posting a score, GET `/proof/{username}/status`
2. **Expected:** Response includes `attestation` block (when signing key is available)

### TC07: Multiple users have independent proof statuses
1. Set proof statuses for alice (proof_generated), bob (pending), charlie (failed)
2. GET `/proof/alice/status` — status is `proof_generated`
3. GET `/proof/bob/status` — status is `pending`
4. GET `/proof/charlie/status` — status is `failed`
5. GET `/proof/dave/status` — status is `unknown`

### TC08: Proof status dashboard — queue depth gauge
1. Set multiple proofs with different statuses
2. Call `ProofStatusStore.count_by_status()`
3. **Expected:** Correct counts per status (e.g., pending=2, proof_generating=2, failed=1)

### TC09: Prover network down — score unaffected
1. Simulate prover network being unreachable
2. Send `POST /score` with a username
3. **Expected:** HTTP 200 with attestation and score
4. GET `/proof/{username}/status`
5. **Expected:** status is `unknown` (enqueue never set a status)

### TC10: Missing GITHUB_TOKEN returns proper error
1. Unset GITHUB_TOKEN environment variable
2. Send `POST /score` with any username
3. **Expected:** HTTP 400 with `"GITHUB_TOKEN"` in error detail

## UAT Type
- Integration / Smoke Test (all critical paths pass 286 automated tests)
- Failure Mode Validation (10 documented failure modes)

## Not Proven By This UAT
- Actual on-chain deployment (requires wallet funding with ~0.01 Base Sepolia ETH)
- Real SP1 prover execution (requires installed prover CLI binary)
- Production Redis/Celery deployment under load
- Proof auto-submission to Base Sepolia after generation (manual step for now)
