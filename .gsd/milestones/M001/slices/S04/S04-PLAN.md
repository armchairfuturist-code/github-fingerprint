# S04: Integration & Polish

**Goal:** Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates. The GITHUB_TOKEN check is deferred from module import to first use, enabling tests to run without the env var. The frontend shows score, signal breakdown, attestation block, and role selector. Integration tests prove the full pipeline works end-to-end.
**Demo:** Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates.

## Must-Haves

- 1. All 161+ existing tests pass (no regressions). 2. Tests run without GITHUB_TOKEN set (module import doesn't crash). 3. Integration tests verify: POST /score returns + attestation verifiable via POST /verify. 4. Frontend shows score, signal breakdown, role selector loaded from /profiles, attestation block. 5. Full test suite passes with `python -m pytest tests/ -v`.

## Proof Level

- This slice proves: final-assembly

## Integration Closure

Upstream surfaces consumed: api/main.py (all endpoints + attestation wiring), crawler/github_api.py (get_user_activity with deep data), scoring/engine.py (role-adaptive score), scoring/profiles.py (profile list), attest/ (signing/verification). New wiring introduced: lazy _get_github_client() replaces module-level GITHUB_TOKEN check; frontend now loads profiles from /profiles API on startup; end-to-end integration tests exercise the full crawl→score→attest→verify pipeline. What remains before the milestone is truly usable end-to-end: nothing — this is the final assembly slice.

## Verification

- Runtime signals: structured warning log when GITHUB_TOKEN is not configured (first attempted use). Inspection surfaces: /health endpoint for liveness, /profiles for available role profiles, /verify for attestation validation. Failure visibility: GITHUB_TOKEN missing → 500 with clear error message; attestation key missing → attestation omitted from response with warning log. Redaction constraints: no PII/secret exposure in logs.

## Tasks

- [x] **T01: Defer GITHUB_TOKEN validation to lazy initialization** `est:30m`
  Move the module-level GITHUB_TOKEN check in api/main.py from import-time to first-use. Currently, `raise ValueError("GITHUB_TOKEN environment variable is required")` runs at module import, preventing pytest from even importing the module when the env var is unset. Replace with a lazy _get_github_client() function that validates and initializes on first call. Update endpoint handlers to call _get_github_client().get_user_activity() instead of referencing the module-level variable. Update test_api.py monkeypatch targets to use 'api.main._get_github_client' instead of the old module variable. Change the ScoreAttestation tests to create a mock client with get_user_activity. This is a structural fix — no behavior changes when GITHUB_TOKEN is set.
  - Files: `api/main.py`, `tests/test_api.py`
  - Verify: python -m pytest tests/ -x -v 2>&1 | tail -5

- [x] **T02: Add end-to-end integration test suite** `est:45m`
  Create tests/test_integration.py with a comprehensive end-to-end test suite covering the full crawl → score → attest → verify flow. The test mocks github_client.get_user_activity to return realistic deep data (with readmes, cicd_configs, and contributions keys as produced by S01) and: (1) Tests POST /score returns overall_score, signal_scores with all 12 signal keys, profile, details, and attestation block. (2) Tests POST /verify round-trips the attestation to confirm valid=true. (3) Tests POST /score?role=marketing returns different scores. (4) Tests GET /score/{username} works with query params. (5) Tests POST /match returns role+matching with attestation. (6) Tests GET /profiles returns profile list. (7) Tests error handling (invalid role = 400, missing username = 400). (8) Tests attestation payload contains all expected fields and is verifiable.
  - Files: `tests/test_integration.py`
  - Verify: python -m pytest tests/test_integration.py -v 2>&1 | tail -10

- [x] **T03: Upgrade frontend to full end-to-end user experience** `est:1h`
  Upgrade index.html from a basic match-only UI to a complete end-to-end experience. Fix the API path (remove /api prefix). Add: (1) Tab/mode selector: Score vs Match. (2) Score mode with GitHub username input and role dropdown (populated from GET /profiles on page load). (3) Score result display: large overall score, 12-signal breakdown with score bars, risk flag list, profile name. (4) Attestation block display: signature (truncated), public_key (truncated), signed_at timestamp, copy-to-clipboard for sharing. (5) Match mode keeps existing functionality but fixes API paths. (6) Loading states, error handling, responsive layout. (7) Preserve existing dark monospace aesthetic.
  - Files: `index.html`
  - Verify: python -c 'assert open("index.html").read().count("</div>") > 20' && grep -q '/profiles' index.html && grep -q 'attestation' index.html

- [x] **T04: Run regression suite and verify all tests pass** `est:15m`
  Run the full test suite to confirm all existing tests still pass after the GITHUB_TOKEN refactor in T01 and the new integration tests from T02 pass. Fix any regressions. Verify: (1) 'python -m pytest tests/ -v' passes with exit code 0. (2) All 4 test files (test_crawler.py, test_scoring.py, test_api.py, test_attest.py, test_integration.py) are included. (3) Test count is >= 161 (pre-S04 baseline) + new integration tests.
  - Files: `tests/test_api.py`, `tests/test_crawler.py`, `tests/test_scoring.py`, `tests/test_attest.py`, `tests/test_integration.py`
  - Verify: python -m pytest tests/ -v 2>&1 | tail -5

## Files Likely Touched

- api/main.py
- tests/test_api.py
- tests/test_integration.py
- index.html
- tests/test_crawler.py
- tests/test_scoring.py
- tests/test_attest.py
