---
estimated_steps: 31
estimated_files: 2
skills_used: []
---

# T04: Comprehensive tests for role-adaptive scoring

Why: The role-adaptive scoring system introduces multiple code paths (3 profiles, confidence filtering, weight redistribution, API contracts). Each path needs test coverage to prevent regressions. This task adds 15+ tests covering profile definitions, scoring behavior, confidence thresholds, API contracts, and backward compatibility.

Files: `tests/test_scoring.py`, `tests/test_api.py` (new file for API endpoint tests)

Do:
1. Add profile definition tests to test_scoring.py:
   - test_profile_definitions_weights_sum_to_one: each profile's weights sum to 1.0 (within tolerance)
   - test_profile_definitions_all_signals_covered: each profile has all 12 signals
   - test_profile_definitions_thresholds_exist: every signal has a confidence threshold
   - test_get_profile_valid: returns correct profile by name
   - test_get_profile_invalid: raises ValueError for unknown name
   - test_list_profiles: returns >= 3 profiles
   - test_resolve_role_profile_none: returns engineering when role=None
2. Add scoring behavior tests to test_scoring.py:
   - test_scoring_engine_with_role_engineering: scores match expected values with engineering weights
   - test_scoring_engine_with_role_marketing: scores differ from engineering for same data
   - test_scoring_engine_role_switching: switching roles changes weights correctly
   - test_confidence_threshold_filtering: signals below threshold excluded from total
   - test_confidence_threshold_all_below: handles all signals below gracefully (returns 0 or neutral)
   - test_score_user_with_role_param: score_user('role') uses correct profile
   - test_score_user_backward_compatible: score_user() without role = same as default
   - test_generate_risk_flags_with_confidence_thresholds: flags for low-confidence signals
3. Create tests/test_api.py with FastAPI TestClient tests:
   - test_profiles_endpoint: GET /profiles returns 200 with list of profiles
   - test_score_with_role: POST /score with role param works
   - test_score_invalid_role: POST /score with bad role returns 400
   - test_match_with_role: POST /match with role uses profile-based matching
4. Ensure all existing tests still pass after adding new tests.

Constraints:
- New tests must not require network or GITHUB_TOKEN
- Use mock SignalResult objects for scoring tests (existing pattern)
- API tests should use TestClient with mocked GitHubAPIClient
- All tests must pass with `python -m pytest tests/ -v`

## Inputs

- `tests/test_scoring.py`
- `scoring/profiles.py`
- `scoring/engine.py`
- `api/main.py`

## Expected Output

- `tests/test_scoring.py`
- `tests/test_api.py`

## Verification

python -m pytest tests/ -v --tb=short 2>&1 | tail -5
