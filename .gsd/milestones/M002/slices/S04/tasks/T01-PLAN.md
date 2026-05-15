---
estimated_steps: 11
estimated_files: 3
skills_used: []
---

# T01: Create scoring-cross-compare crate

Create a new Rust binary crate `scoring-cross-compare` that feeds identical ScoreInput JSON fixtures to both scoring_core::engine::score_user and scoring_sp1_core::score_user, then compares every signal score + confidence + details + overall_score + risk_flags with zero tolerance (exact f64 equality). Add to workspace members.

**Cargo.toml dependencies:** scoring-types, scoring-core, scoring-sp1-core, serde_json, clap (optional — simple arg parsing).

**main.rs structure:**
1. Accept `--fixture <path>` (single) or `--all-fixtures` (scans `py-scoring-ref/fixtures/*.json`)
2. For each fixture:
   - Read and parse ScoreInput JSON
   - Call `scoring_core::engine::score_user(&input, None)` → reference
   - Call `scoring_sp1_core::score_user(&input, None)` → test
   - Compare: overall_score (exact ==), signal_scores (each name/score/confidence, exact == for f64 values), details BTreeMap keys/values, risk_flags, profile_name, signals_below_threshold, signals_scored
3. Print per-signal PASS/FAIL lines with diff values on mismatch
4. Exit 0 if all PASS, 1 on any FAIL

## Inputs

- `Cargo.toml`
- `scoring-core/Cargo.toml`
- `scoring-core/src/lib.rs`
- `scoring-core/src/engine.rs`
- `scoring-sp1-core/Cargo.toml`
- `scoring-sp1-core/src/lib.rs`
- `scoring-sp1-core/src/engine.rs`
- `scoring-types/src/lib.rs`

## Expected Output

- `scoring-cross-compare/Cargo.toml`
- `scoring-cross-compare/src/main.rs`

## Verification

cargo build -p scoring-cross-compare
