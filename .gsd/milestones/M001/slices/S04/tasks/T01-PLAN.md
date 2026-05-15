---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T01: Defer GITHUB_TOKEN validation to lazy initialization

Move the module-level GITHUB_TOKEN check in api/main.py from import-time to first-use. Currently, `raise ValueError("GITHUB_TOKEN environment variable is required")` runs at module import, preventing pytest from even importing the module when the env var is unset. Replace with a lazy _get_github_client() function that validates and initializes on first call. Update endpoint handlers to call _get_github_client().get_user_activity() instead of referencing the module-level variable. Update test_api.py monkeypatch targets to use 'api.main._get_github_client' instead of the old module variable. Change the ScoreAttestation tests to create a mock client with get_user_activity. This is a structural fix — no behavior changes when GITHUB_TOKEN is set.

## Inputs

- `api/main.py`
- `tests/test_api.py`

## Expected Output

- `api/main.py`
- `tests/test_api.py`

## Verification

python -m pytest tests/ -x -v 2>&1 | tail -5
