---
id: T03
parent: S02
milestone: M002
key_files:
  - api/prover_client.py
  - api/main.py
  - api/__init__.py
  - tests/test_prover_client.py
key_decisions:
  - Used FastAPI BackgroundTasks for non-blocking proof generation after score response
  - Used SHA-256 hash of username|timestamp for persistent proof_id
  - Used try/except import fallback for dual package/direct-execution contexts
duration: 
verification_result: passed
completed_at: 2026-05-12T08:30:43.237Z
blocker_discovered: false
---

# T03: Created Python prover client wrapper (run_proof) with BackgroundTasks integration in the /score endpoint, ScoreInput JSON builder, 26-unit test suite

**Created Python prover client wrapper (run_proof) with BackgroundTasks integration in the /score endpoint, ScoreInput JSON builder, 26-unit test suite**

## What Happened

Created api/prover_client.py with the run_proof(username, activity_data) function that: (1) builds a ScoreInput JSON dict from crawl activity data using _build_score_input(), (2) writes it to a temp file, (3) invokes scoring-prover-cli --input <tmpfile> as subprocess, (4) parses the metadata JSON from stdout, (5) returns a dict with proof_id, status, proving_time_ms, proving_time_seconds, prover, proof_path, and input_summary. Error handling covers FileNotFoundError, TimeoutExpired, non-zero exit codes, and non-JSON stdout with fallback to wall-clock timing. FastAPI BackgroundTasks was wired into the /score POST endpoint so proof generation fires asynchronously after the score response is sent. A proof_id (SHA-256 of username|timestamp) is included in the ScoreResponse. The api/__init__.py was added to make the directory a proper package, and a try/except import fallback handles both package and direct-execution contexts. 26 new unit tests cover serialization helpers, ScoreInput builder, proof_id generation, and all run_proof error paths. All 224 tests pass.

## Verification

1. python -m pytest tests/test_prover_client.py -v — 26/26 passed, covering serialization, ScoreInput builder, proof_id generation, subprocess happy path, CLI failure, binary-not-found, timeout, non-JSON stdout fallback, input_summary, and missing proof_path 2. python -m pytest tests/ — 224/224 passed (198 original + 26 new) 3. Import verification: api/main.py successfully imports run_proof and _generate_proof_id from prover_client 4. BackgroundTasks wiring: /score POST endpoint accepts background_tasks parameter; GET endpoint passes BackgroundTasks() explicitly to the POST handler

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_prover_client.py -v` | 0 | ✅ pass | 50ms |
| 2 | `python -m pytest tests/ -v` | 0 | ✅ pass | 890ms |
| 3 | `python -c "from api.main import app"` | 0 | ✅ pass | 200ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/prover_client.py`
- `api/main.py`
- `api/__init__.py`
- `tests/test_prover_client.py`
