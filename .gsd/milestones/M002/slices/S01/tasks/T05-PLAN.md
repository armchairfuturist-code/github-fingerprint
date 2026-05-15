---
estimated_steps: 10
estimated_files: 3
skills_used: []
---

# T05: Build CLI and Python comparison script

Build a CLI binary in scoring-cli:
- Reads ScoreInput JSON from stdin or file
- Calls the Rust scoring engine
- Outputs ScoreOutput JSON to stdout

Build a Python comparison script (py-scoring-ref/compare.py):
- Uses existing Python scoring engine
- Runs both Rust and Python on the same test inputs
- Produces a diff report: per-signal score diff, overall score diff, risk flag diff
- Exit code 0 if all scores match within ±0.5

Build 5 representative ScoreInput fixtures (serialized JSON files from actual/cached GitHub profiles)

## Inputs

- `scoring/engine.py`
- `scoring/profiles.py`
- `signals/extractor.py`

## Expected Output

- `scoring-cli/src/main.rs`
- `py-scoring-ref/compare.py`
- `py-scoring-ref/fixtures/profile1.json`
- `py-scoring-ref/fixtures/profile2.json`
- `py-scoring-ref/fixtures/profile3.json`
- `py-scoring-ref/fixtures/profile4.json`
- `py-scoring-ref/fixtures/profile5.json`

## Verification

cargo run -- --input py-scoring-ref/fixtures/profile1.json outputs valid ScoreOutput JSON. python py-scoring-ref/compare.py reports all scores matching within tolerance.
