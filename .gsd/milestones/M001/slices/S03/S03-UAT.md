# S03: Attestation Upgrade — UAT

**Milestone:** M001
**Written:** 2026-05-12T06:31:47.833Z

## UAT: Attestation End-to-End Verification

### Preconditions
- A valid Ed25519 signing key exists (auto-generated on first run)
- The API server is running with `GITHUB_TOKEN` set
- No prior attestation state required

### Test 1: /score response includes attestation
1. POST /score with `{"username": "octocat"}`
2. Verify response status is 200
3. Verify `attestation` block is present and non-null
4. Verify `attestation.signature` is a non-empty base64 string
5. Verify `attestation.public_key` is a non-empty base64 string
6. Verify `attestation.signed_payload` is a valid JSON string
7. Verify `attestation.signed_at` is a valid ISO 8601 timestamp
**Expected:** All fields present and well-formed

### Test 2: Attestation payload contains correct identity
1. POST /score with `{"username": "attestuser"}`
2. Parse `attestation.signed_payload` as JSON
3. Verify `payload.username` equals `"attestuser"`
4. Verify `payload.overall_score` is a float between 0 and 100
5. Verify `payload.signal_scores` is a non-empty object
6. Verify `payload.profile_name` is a string
**Expected:** Payload accurately reflects the scored user and their results

### Test 3: Tampered payload fails verification
1. POST /score with any valid username
2. Extract `attestation.public_key` and `attestation.signature`
3. POST /verify with `signed_payload='{"tampered": true}'` + correct `signature` + correct `public_key`
4. Verify response status is 200
5. Verify `valid` is `false`
6. Verify `error` message is present
**Expected:** Modified payloads are correctly rejected

### Test 4: Valid signature verifies via /verify endpoint
1. POST /score with `{"username": "verifytest"}`
2. Extract all three fields from `attestation`
3. POST /verify with same `signed_payload`, `signature`, `public_key`
4. Verify `valid` is `true`
5. Verify `payload.username` equals `"verifytest"`
**Expected:** Valid signatures verify successfully, returning the original payload

### Test 5: /match response also includes attestation
1. POST /match with `{"username": "testuser", "role_description": "engineering"}`
2. Verify response status is 200
3. Verify `attestation` block is present with all 4 fields
4. Verify payload contains correct `username` and `role`
**Expected:** Both /score and /match produce attested responses

### Test 6: /verify with missing fields returns 422
1. POST /verify with `{}` (empty body)
2. Verify response status is 422
3. POST /verify with `{"signed_payload": "..."}` only (missing signature and public_key)
4. Verify response status is 422
**Expected:** FastAPI's built-in Pydantic validation catches missing required fields

### Edge Cases
- **Missing signing key:** Remove or corrupt the signing key file, restart server — /score and /match responses should omit the attestation block (graceful degradation) with a server log warning
- **Wrong public key:** Submit a valid signature with a different public_key to /verify — should return `valid: false`
- **Empty signed_payload:** Verify with empty string payload — should return `valid: false` with error

### UAT Type
Contract + Integration

### Not Proven By This UAT
- Cryptographic strength of Ed25519 (implicit in the algorithm, not the implementation)
- Performance under concurrent load (not scoped for this slice)
- Key rotation and revocation workflows (future concern)

