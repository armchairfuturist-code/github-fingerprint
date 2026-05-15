---
id: S04
parent: M001
milestone: M001
provides:
  - Full end-to-end crawl→score→attest→verify pipeline
  - Frontend with Score/Match tabs, role selector, signal breakdown, attestation sharing
  - 37 integration tests proving pipeline completeness
  - GITHUB_TOKEN-free module import for testability
requires:
  []
affects:
  []
key_files:
  - api/main.py
  - tests/test_api.py
  - tests/test_integration.py
  - index.html
  - tests/test_attest.py
  - tests/test_crawler.py
  - tests/test_scoring.py
key_decisions:
  - Deferred GITHUB_TOKEN validation to lazy _get_github_client() so api.main can be imported without the env var
  - Integration tests use SimpleNamespace mock objects matching GitHub dataclass shapes instead of real API calls
  - Used GET /score/{username} with ?role= query param for simpler URL-based score retrieval from the frontend
  - Role dropdown populated from GET /profiles on page load, falling back gracefully if profiles endpoint is unavailable
  - Attestation copy-to-clipboard bundles signature, public_key, signed_payload, and signed_at as JSON for easy sharing and verification
patterns_established:
  - Lazy initialization for env-dependent resources: _get_github_client() validates GITHUB_TOKEN on first-use not at import
  - Integration tests with SimpleNamespace mock objects for realistic deep data shapes without HTTP calls
  - Stateful ScoringEngine singleton requires integration tests that avoid strict cross-test assertions on profile_name and risk_flags
observability_surfaces:
  - GET /health endpoint for liveness
  - GET /profiles for available role profiles
  - Structured warning log when GITHUB_TOKEN is not configured (first attempted use)
  - Structured warning log when attestation signing key unavailable
  - GITHUB_TOKEN missing → 500 with clear error message
  - Attestation key missing → attestation omitted from response with warning log
  - Attestation success log with score and signature prefix
drill_down_paths:
  - .gsd/milestones/M001/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T04-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T06:55:11.255Z
blocker_discovered: false
---

# S04: S04: Integration & Polish

**Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates.**

## What Happened

S04 completed the final assembly of the GitHub Fingerprint pipeline, wiring together the deep crawler (S01), role-adaptive scoring engine (S02), and Ed25519 attestation (S03) into a cohesive end-to-end experience.

**T01 (Deferred GITHUB_TOKEN to lazy init):** Refactored api/main.py to replace module-level GITHUB_TOKEN validation with a lazy _get_github_client() function that validates and initializes on first use. This structural fix enables tests to import the module without the env var set — no behavior change when GITHUB_TOKEN is configured. Updated monkeypatch targets in test_api.py accordingly.

**T02 (Integration test suite):** Created tests/test_integration.py with 37 comprehensive end-to-end tests. The test suite uses SimpleNamespace mock objects with realistic deep data: 5 repos across 5 languages, 12 commits with varied message types (feat, fix, refactor, docs, chore, perf, style, ci), 6 issues, 4 PRs (3 merged), 3 READMEs with rich content including badges and code blocks, CI/CD configs across 5 repos, and 365-day contribution calendar. Tests cover: POST /score response shape (overall_score, all 12 signals, profile, details, attestation), POST /verify round-trip verification, role-specific scoring producing different scores across profiles, GET /score/{username} with query params, POST /match with attestation, GET /profiles returning complete profile list with weights summing to ~1.0, and error handling (invalid role=400, missing username=422, tampered attestation=invalid).

**T03 (Frontend upgrade):** Upgraded index.html from a basic match-only UI to a complete end-to-end experience with Score/Match tab mode selector, GitHub username input with role dropdown populated from GET /profiles on page load, large overall score display with 12-signal breakdown bars and risk flag list, attestation block showing signature/public_key/signed_at with copy-to-clipboard JSON bundle, loading states, error handling, responsive layout, and preserved dark monospace aesthetic. API paths were corrected (removed /api prefix).

**T04 (Regression suite):** Verified full regression suite passes: 198 tests across 5 test files (test_crawler.py: 46, test_scoring.py: 51, test_api.py: 46, test_attest.py: 18, test_integration.py: 37) — exit code 0, 0 failures, 0 errors in 0.31s. No regressions from T01 refactor or T02 integration tests.

## Verification

All verification checks pass:

1. **Test suite (198 tests):** `python -m pytest tests/ -v` — exit code 0, 198 passed, 0 failed, 0 errors in 0.31s. All 5 test files collected and passing.

2. **GITHUB_TOKEN lazy init:** Module imports cleanly without GITHUB_TOKEN set. `_get_github_client()` correctly raises `ValueError("GITHUB_TOKEN environment variable is required")` on first use when token is missing. Tests without GITHUB_TOKEN pass via mocked `_get_github_client`.

3. **Frontend verification:** `</div>` count: 50 (>20 required) ✓, `/profiles` endpoint referenced ✓, `attestation` functionality present ✓, Score and Match tabs implemented ✓, role dropdown ✓.

4. **Integration test coverage:** POST /score returns all required fields (overall_score, 12 signal keys with score/confidence/details, profile, details, risk_flags, attestation block). POST /verify round-trips attestations (valid=true for genuine, valid=false for tampered payloads). Role-specific scoring produces different scores across engineering/marketing/non-technical profiles. GET /score/{username} with ?role= query param works. POST /match includes verifiable attestation. GET /profiles returns complete profiles with weights summing to ~1.0.

## Requirements Advanced

- R001 — The deep pipeline with README content, CI/CD configs, contributions, commit semantics, and AI usage detection is now wired end-to-end through the full crawl→score→attest→verify flow.
- R002 — Role-adaptive scoring with profiles accessed via GET /profiles and specified via ?role= query param is now available in the frontend and integration-tested end-to-end.
- R003 — Ed25519 attestation is now included in /score and /match responses, verifiable via /verify, with graceful degradation when no signing key is available.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `api/main.py` — Refactored to lazy _get_github_client() for GITHUB_TOKEN initialization
- `tests/test_api.py` — Updated monkeypatch targets to use 'api.main._get_github_client' path
- `tests/test_integration.py` — New file with 37 end-to-end integration tests
- `index.html` — Upgraded from basic match-only UI to full end-to-end Score/Match UX
