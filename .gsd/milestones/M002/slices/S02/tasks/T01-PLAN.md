---
estimated_steps: 8
estimated_files: 2
skills_used: []
---

# T01: Create SP1 zkVM program wrapping scoring lib

Create an SP1 zkVM program in scoring-sp1/ that:
- Depends on the scoring-core lib crate
- Has an entrypoint that reads serialized ScoreInput from stdin
- Calls ScoringEngine::score() to produce a ScoreOutput
- Writes ScoreOutput to stdout (for verification) and commits to the public output stream
- Executes entirely within the RISC-V guest (no std::fs, no networking)

Set up: install sp1up (SP1 toolchain), create program/ and script/ directories.

Output: `cargo prove build` succeeds. Program runs `echo '{}' | cargo prove run` without crashing.

## Inputs

- `scoring-core/ (Rust scoring lib from S01)`

## Expected Output

- `scoring-sp1/program/Cargo.toml`
- `scoring-sp1/program/src/main.rs`
- `scoring-sp1/script/Cargo.toml`
- `scoring-sp1/script/src/main.rs`

## Verification

cargo prove build passes. cargo prove run produces valid output. No std-only dependencies used in program/guest.
