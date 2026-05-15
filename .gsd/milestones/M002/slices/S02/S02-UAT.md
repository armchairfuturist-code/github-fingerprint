# S02: SP1 Prover Pipeline — UAT

**Milestone:** M002
**Written:** 2026-05-12T08:33:54.540Z

## UAT Type

- **UAT mode:** artifact-driven
- **Why this mode is sufficient:** This slice produces source code that cannot be fully executed on Windows (SP1 toolchain unavailable). Verification is based on code completeness, structural correctness, Rust compilation (scoring-sp1-core), and Python test suite (224/224 pass).

## Preconditions

- Python 3.11+ with project dependencies installed
- Rust toolchain installed (for scoring-sp1-core compilation check)
- Linux/macOS host required for full SP1 proof generation

## Smoke Test

```bash
python -m pytest tests/test_prover_client.py -v
# Expected: 26/26 passed
```

## Test Cases

### 1. Python prover client unit tests pass
1. Run `python -m pytest tests/test_prover_client.py -v`
2. **Expected:** All 26 tests pass covering: ScoreInput builder, proof_id generation, subprocess happy path, CLI failure, binary-not-found, timeout, non-JSON stdout fallback, input_summary, missing proof_path

### 2. Full test suite regression
1. Run `python -m pytest tests/ -v`
2. **Expected:** 224/224 passed (no regressions from S02 changes)

### 3. Import verification
1. Run `python -c "from api.prover_client import run_proof, _build_score_input, _generate_proof_id"`
2. **Expected:** No import errors

### 4. scoring-sp1-core compiles (no_std)
1. Run `cargo build -p scoring-sp1-core`
2. **Expected:** Compilation succeeds

### 5. Key files exist
1. Verify existence of: scoring-sp1-core/src/lib.rs, scoring-sp1/program/src/main.rs, scoring-sp1/script/src/main.rs, scoring-prover-cli/src/main.rs, api/prover_client.py
2. **Expected:** All files present

## Edge Cases

### Error handling — missing scoring-prover-cli binary
1. Ensure the CLi binary is not in PATH
2. Call run_proof with valid data
3. **Expected:** Returns error metadata with status "error: binary-not-found" and descriptive error message

### Error handling — timeout
1. The prover client has a 300-second timeout for subprocess calls
2. **Expected:** Timeout is handled gracefully with non-JSON stdout fallback

## Failure Signals

- Any test failure in test_prover_client.py or the full test suite
- Missing SP1 program structure files
- Import errors from api/prover_client.py into api/main.py
- Rust compilation errors in scoring-sp1-core

## Not Proven By This UAT

- Full proof generation (requires SP1 toolchain on Linux/macOS with `cargo prove build`)
- Cycle count and proving time benchmarks
- Succinct Prover Network connectivity
- Celery worker integration (CI/CD integration not yet implemented)
- Groth16 proof format compatibility with Solidity verifier (S03 scope)

## Notes for Tester

This slice produces code that bridges Rust/SP1 and Python. The SP1 toolchain is not available on Windows. The Rust workspace compiles on Linux/macOS with `cargo prove build scoring-sp1`. The scoring-prover-cli binary is the intended subprocess target from the Python wrapper. The SP1_PROVER env var controls proving backend: unset or "local" for CPU proving, "network" for Succinct Prover Network.
