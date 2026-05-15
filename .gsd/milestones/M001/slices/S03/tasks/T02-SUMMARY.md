---
id: T02
parent: S03
milestone: M001
key_files:
  - api/main.py
key_decisions:
  - Attestation helper (_build_attestation) centralized as module-level function to avoid duplication between /score and /match endpoints
  - verify_key_bytes exported as module-level variable for /verify endpoint access
  - Global _signing_key set to None on init failure — all downstream callers check before using
duration: 
verification_result: passed
completed_at: 2026-05-12T06:13:42.809Z
blocker_discovered: false
---

# T02: Wired Ed25519 attestation into ScoreResponse/MatchResponse models and /score and /match endpoints with graceful degradation when signing key is unavailable

**Wired Ed25519 attestation into ScoreResponse/MatchResponse models and /score and /match endpoints with graceful degradation when signing key is unavailable**

## What Happened

Added attestation support to the FastAPI API layer:

1. Added `attestation: Optional[Dict[str, Any]] = None` field to both `ScoreResponse` and `MatchResponse` Pydantic models, so attestation blocks are optional and absent by default.

2. Created `_build_attestation()` helper function that wraps `sign_score()` with graceful error handling — logs a warning if the signing key is None, logs success with signature prefix when signing works, and logs an exception on unexpected failures. Always returns `None` (omitting attestation) rather than crashing.

3. Wired `_build_attestation()` into the `/score` POST endpoint after computing the score result, passing username, overall_score, normalized signal_scores, risk_flags, and profile_name.

4. Wired `_build_attestation()` into the `/match` POST endpoint similarly — normalizes SignalResult objects into dicts first, then produces the attestation block.

5. Initialized attestation at module level with a try/except around `load_or_generate_signing_key()` — on failure, both `_signing_key` and `verify_key_bytes` are set to None and attestation is silently omitted from responses.

6. Exported `verify_key_bytes` as a module-level variable so the future `/verify` endpoint can access the public key bytes.

## Verification

All 147 existing pytest tests pass (no regressions). `grep -q "attestation" api/main.py` passes. Manual verification confirmed: ScoreResponse and MatchResponse both accept attestation blocks, attestation defaults to None when omitted, _build_attestation produces full 4-field attestation blocks (signature, public_key, signed_payload, signed_at) when key is available, and returns None gracefully when signing key is missing.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/ -v --tb=short` | 0 | ✅ pass (147/147) | 200ms |
| 2 | `grep -q 'attestation' api/main.py` | 0 | ✅ pass | 10ms |
| 3 | `python -c '... attestation wiring validation ...'` | 0 | ✅ pass (5 checks) | 300ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/main.py`
