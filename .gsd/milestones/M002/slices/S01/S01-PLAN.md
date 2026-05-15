# S01: Rust Scoring Library

**Goal:** Port the Python scoring engine (12 signals, role-adaptive weights, confidence thresholding) to a Rust library crate with serde JSON I/O, verified against the Python reference. This is the foundation for SP1 proving — the Rust lib must compile to RISC-V and stay within SP1's cycle budget.
**Demo:** cargo test passes all signal tests; Python vs Rust comparison shows exact match across all 12 signals for multiple GitHub profiles

## Must-Haves

- All 12 signals ported with matching output vs Python reference
- Role-adaptive profiles (engineering, marketing, non-technical) with confidence thresholding
- serde JSON serialization for ScoreInput/ScoreOutput
- CI comparison script validates against Python reference daily
- Cycle count within SP1 feasibility range (< 10M RISC-V cycles for typical inputs)

## Proof Level

- This slice proves: Full — Rust crate with cargo test + cross-language comparison script producing a diff report showing exact match across 5+ GitHub profiles

## Integration Closure

Provides the Rust scoring lib that S02 wraps in an SP1 program. The serde JSON input format must match what the FastAPI /score endpoint produces today (activity_data dict with repos/commits/issues/prs).

## Verification

- Structured logging of signal scores per profile type. Comparison script writes diffs to a report file. Cycle count report at the end.

## Tasks

- [x] **T01: Set up Rust project structure** `est:1h`
  Create Cargo workspace with:
  - scoring-core/ — lib crate: port scoring engine + profiles
  - scoring-signals/ — lib crate: port signal extraction
  - scoring-cli/ — binary crate: CLI that reads ScoreInput JSON → outputs ScoreOutput JSON
  - Files: `Cargo.toml`, `scoring-core/Cargo.toml`, `scoring-core/src/lib.rs`, `scoring-signals/Cargo.toml`, `scoring-signals/src/lib.rs`, `scoring-cli/Cargo.toml`, `scoring-cli/src/main.rs`
  - Verify: cargo build && cargo test passes. Directory structure mirrors Python layout.

- [x] **T02: Define Rust data types (ScoreInput/ScoreOutput/Profile)** `est:30m`
  Define the data types in scoring-core:
  - ScoreInput: mirrors the activity_data dict shape from Python (repos, commits, issues, prs)
  - SignalScore: struct with score, confidence, details (HashMap<String, serde_json::Value>)
  - ScoreOutput: struct with overall_score, signal_scores, risk_flags, profile_name, signals_below_threshold
  - SignalConfig: name, weight, confidence_threshold
  - RoleProfile: struct with name, display_name, description, weights, confidence_thresholds
  - Files: `scoring-core/src/types.rs`, `scoring-core/src/lib.rs`
  - Verify: cargo build. Unit test: create each struct, serialize to JSON, deserialize back, verify fields match.

- [x] **T03: Port all 12 signals to Rust** `est:3h`
  Port all 12 signals from Python signals/extractor.py to Rust scoring-signals crate:
  - Files: `scoring-signals/src/*.rs`
  - Verify: cargo test. Every signal produces valid output for a sample ScoreInput. Compare output against Python reference for the same input.

- [x] **T04: Port scoring engine and role profiles to Rust** `est:1.5h`
  Port the scoring engine from scoring/engine.py to Rust scoring-core:
  - ScoringEngine struct with weights HashMap, confidence_thresholds, role_profile
  - calculate_overall_score(): confidence filtering, proportional weight redistribution
  - generate_risk_flags(): low scores, low confidence, threshold violations
  - set_role(): load profile weights/thresholds
  - score(): full pipeline: extract signals → calculate → risk flags → ScoreOutput
  - Files: `scoring-core/src/engine.rs`, `scoring-core/src/profiles.rs`, `scoring-core/src/lib.rs`
  - Verify: cargo test. Run 5 test profiles through Rust engine, compare against Python engine output. Scores match within ±0.5. Risk flags match.

- [x] **T05: Build CLI and Python comparison script** `est:1.5h`
  Build a CLI binary in scoring-cli:
  - Reads ScoreInput JSON from stdin or file
  - Calls the Rust scoring engine
  - Outputs ScoreOutput JSON to stdout
  - Files: `scoring-cli/src/main.rs`, `py-scoring-ref/compare.py`, `py-scoring-ref/fixtures/*.json`
  - Verify: cargo run -- --input py-scoring-ref/fixtures/profile1.json outputs valid ScoreOutput JSON. python py-scoring-ref/compare.py reports all scores matching within tolerance.

- [x] **T06: Cycle count profiling for SP1 feasibility** `est:1h`
  Add a cycle count estimation step:
  - Build a minimal SP1 program stub (no prover) that calls the Rust scoring lib
  - Use SP1's `sp1-helper` or manual approach to get RISC-V cycle count
  - Report cycle count in an analysis doc
  - If cycles > 10M, identify heaviest signals for optimization
  - Files: `docs/cycle-count-report.md`
  - Verify: Cycle count report documents total cycles, per-signal breakdown, and feasibility verdict.

## Files Likely Touched

- Cargo.toml
- scoring-core/Cargo.toml
- scoring-core/src/lib.rs
- scoring-signals/Cargo.toml
- scoring-signals/src/lib.rs
- scoring-cli/Cargo.toml
- scoring-cli/src/main.rs
- scoring-core/src/types.rs
- scoring-signals/src/*.rs
- scoring-core/src/engine.rs
- scoring-core/src/profiles.rs
- py-scoring-ref/compare.py
- py-scoring-ref/fixtures/*.json
- docs/cycle-count-report.md
