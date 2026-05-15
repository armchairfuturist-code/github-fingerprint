---
estimated_steps: 8
estimated_files: 1
skills_used: []
---

# T03: Python prover client wrapper

Create a Python subprocess wrapper in the FastAPI app:
- run_proof(username: str, score_input: dict) -> dict
- Calls scoring-prover-cli as subprocess
- Returns proof metadata (proof_path, cycle_count, proving_time)

Wire proof generation into the existing score flow:
- After /score returns the Ed25519 response, enqueue proof generation
- Generate a persistent proof_id (hash of username + timestamp)

Output: Python function that triggers proof generation. Not yet wired to Celery — subprocess call for testing.

## Inputs

- `api/main.py`
- `scoring-prover-cli/src/main.rs`

## Expected Output

- `api/prover_client.py`

## Verification

Python subprocess call generates a proof file. Returns correct metadata dict. Error handling works for bad input.
