---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Add end-to-end integration test suite

Create tests/test_integration.py with a comprehensive end-to-end test suite covering the full crawl → score → attest → verify flow. The test mocks github_client.get_user_activity to return realistic deep data (with readmes, cicd_configs, and contributions keys as produced by S01) and: (1) Tests POST /score returns overall_score, signal_scores with all 12 signal keys, profile, details, and attestation block. (2) Tests POST /verify round-trips the attestation to confirm valid=true. (3) Tests POST /score?role=marketing returns different scores. (4) Tests GET /score/{username} works with query params. (5) Tests POST /match returns role+matching with attestation. (6) Tests GET /profiles returns profile list. (7) Tests error handling (invalid role = 400, missing username = 400). (8) Tests attestation payload contains all expected fields and is verifiable.

## Inputs

- `api/main.py`
- `tests/test_api.py`

## Expected Output

- `tests/test_integration.py`

## Verification

python -m pytest tests/test_integration.py -v 2>&1 | tail -10
