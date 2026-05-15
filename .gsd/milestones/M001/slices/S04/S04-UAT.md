# S04: S04: Integration & Polish — UAT

**Milestone:** M001
**Written:** 2026-05-12T06:55:11.255Z

# UAT: S04 — Integration & Polish

## Preconditions
1. A GITHUB_TOKEN environment variable must be set with a valid GitHub personal access token.
2. The FastAPI server must be running (`python -m uvicorn api.main:app`).
3. An ATTEST_PRIVATE_KEY may optionally be set; if absent, attestation is gracefully omitted.

## UAT Type
Final-assembly integration verification.

## Not Proven By This UAT
- Real GitHub API latency and rate limiting behavior (tested via integration mocks).
- Browser rendering of the frontend in specific browsers (structural correctness verified).
- Long-running session persistence across server restarts.

## Score a User (POST /score)

### Step 1: Score a known GitHub username
**Action:** POST /score with `{"username": "octocat"}`
**Expected:** 200 OK. Response body contains:
- `overall_score`: number 0–100
- `signal_scores`: object with exactly 12 keys (commit_consistency, language_diversity, issue_engagement, pr_patterns, project_ownership, review_patterns, response_time, readme_quality, commit_semantics, cicd_maturity, contribution_consistency, ai_usage_patterns)
- Each signal has: `score` (0–100), `confidence` (0–1), `details` (object)
- `profile`: string (e.g. "engineering")
- `details`: object with `profile_name`, `signals_below_threshold`, `threshold_applied`
- `risk_flags`: array of strings
- `attestation`: object with `signature`, `public_key`, `signed_payload`, `signed_at`

### Step 2: Score with role-specific profile
**Action:** POST /score with `{"username": "octocat", "role": "marketing"}`
**Expected:** 200 OK. `profile` is "marketing". Scores differ from default (engineering) profile.

### Step 3: Request with invalid role
**Action:** POST /score with `{"username": "octocat", "role": "nonexistent"}`
**Expected:** 400 Bad Request. Detail contains "Unknown profile" message.

### Step 4: Request with missing username
**Action:** POST /score with `{}`
**Expected:** 422 Unprocessable Entity (Pydantic validation error).

## Verify Attestation (POST /verify)

### Step 5: Round-trip verification
**Action:** POST /score with `{"username": "verifyuser"}`, then POST /verify with the `signed_payload`, `signature`, and `public_key` from the attestation block.
**Expected:** /verify returns 200 with `{"valid": true, "payload": {"username": "verifyuser", ...}}`.

### Step 6: Tampered payload rejection
**Action:** POST /verify with a tampered payload (e.g., `{"tampered": true}`) but original signature and key.
**Expected:** `valid` is `false`. `error` contains description of mismatch.

## Match User (POST /match)

### Step 7: Match a user to a role
**Action:** POST /match with `{"username": "octocat", "role_description": "engineering"}`
**Expected:** 200 OK. Response contains `match_score`, `top_reasons` (non-empty list), `signal_overview` (with `overall` and `details`), and `attestation`.

### Step 8: Match attestation is verifiable
**Action:** Verify the attestation from Step 7 via POST /verify.
**Expected:** `valid` is `true`.

## GET Endpoints

### Step 9: Score via GET
**Action:** GET /score/octocat?role=marketing
**Expected:** 200 OK. Same response shape as POST /score. `username`="octocat", `profile`="marketing".

### Step 10: List profiles
**Action:** GET /profiles
**Expected:** 200 OK. Response contains `profiles` array with entries having `name`, `display_name`, `description`, `weights`. Includes "engineering", "marketing", "non-technical". Each profile's weights sum to ~1.0.

### Step 11: Health check
**Action:** GET /health
**Expected:** 200 OK. `{"status": "ok", "service": "github-fingerprint-api"}`.

## Edge Cases

### Step 12: Empty username returns error
**Action:** POST /score with `{"username": ""}`
**Expected:** 400, 422, or 500 — error handled gracefully, no crash.

### Step 13: Unknown role description in match
**Action:** POST /match with `{"username": "octocat", "role_description": "xyzzy_unknown_role_123"}`
**Expected:** 200 OK with sensible default scores (engineering profile fallback).

### Step 14: Missing fields in verify
**Action:** POST /verify with `{"signed_payload": "test", "signature": "test"}` (missing public_key).
**Expected:** 422 Unprocessable Entity.

