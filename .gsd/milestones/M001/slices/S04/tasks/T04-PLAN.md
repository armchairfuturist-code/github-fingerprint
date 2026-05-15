---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T04: Run regression suite and verify all tests pass

Run the full test suite to confirm all existing tests still pass after the GITHUB_TOKEN refactor in T01 and the new integration tests from T02 pass. Fix any regressions. Verify: (1) 'python -m pytest tests/ -v' passes with exit code 0. (2) All 4 test files (test_crawler.py, test_scoring.py, test_api.py, test_attest.py, test_integration.py) are included. (3) Test count is >= 161 (pre-S04 baseline) + new integration tests.

## Inputs

- `tests/test_api.py`
- `tests/test_crawler.py`
- `tests/test_scoring.py`
- `tests/test_attest.py`
- `tests/test_integration.py`

## Expected Output

- `tests/test_api.py`
- `tests/test_crawler.py`
- `tests/test_scoring.py`
- `tests/test_attest.py`
- `tests/test_integration.py`

## Verification

python -m pytest tests/ -v 2>&1 | tail -5
