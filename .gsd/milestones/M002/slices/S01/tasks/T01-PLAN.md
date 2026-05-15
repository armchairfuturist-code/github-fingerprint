---
estimated_steps: 7
estimated_files: 7
skills_used: []
---

# T01: Set up Rust project structure

Create Cargo workspace with:
- scoring-core/ — lib crate: port scoring engine + profiles
- scoring-signals/ — lib crate: port signal extraction
- scoring-cli/ — binary crate: CLI that reads ScoreInput JSON → outputs ScoreOutput JSON

Set up Cargo.toml with dependencies: serde, serde_json, thiserror, tracing.
Create py-scoring-ref/ dir for Python reference scripts.

Output: `cargo build` compiles. Directory structure mirrors the Python layout (signals/, scoring/, profiles/).

## Inputs

- `api/main.py (models)`
- `scoring/engine.py`
- `scoring/profiles.py`
- `signals/extractor.py`

## Expected Output

- `scoring-core/src/lib.rs`
- `scoring-signals/src/lib.rs`
- `scoring-cli/src/main.rs`
- `Cargo.toml workspace root`

## Verification

cargo build && cargo test passes. Directory structure mirrors Python layout.
