---
id: T01
parent: S04
milestone: M001
key_files:
  - api/main.py
  - tests/test_api.py
key_decisions:
  - Deferred GITHUB_TOKEN validation to lazy initialization so api.main can be imported without the env var set
  - Tests use string-path monkeypatch of api.main._get_github_client to return a MagicMock
duration: 
verification_result: passed
completed_at: 2026-05-12T06:38:43.780Z
blocker_discovered: false
---

# T01: Deferred GITHUB_TOKEN validation from module-import time to lazy first-use via _get_github_client()

**Deferred GITHUB_TOKEN validation from module-import time to lazy first-use via _get_github_client()**

## What Happened

Replaced the module-level GITHUB_TOKEN check in api/main.py with a lazy _get_github_client() function that validates the token and initializes GitHubAPIClient on first call. Removed the module-level `github_client` variable. Updated the two endpoint handlers (POST /score, POST /match) to call _get_github_client().get_user_activity() instead of the old module variable. Updated all 5 TestScoreAttestation test methods to monkeypatch "api.main._get_github_client" with a MagicMock returning MINIMAL_ACTIVITY, instead of the old pattern that imported the module-level `github_client` variable. All 161 tests pass.

## Verification

All 161 tests pass with `python -m pytest tests/ -x -v`. The module now imports cleanly without GITHUB_TOKEN set. Endpoint tests work via mocked _get_github_client returning a MagicMock client.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/ -x -v` | 0 | ✅ pass | 230ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/main.py`
- `tests/test_api.py`
