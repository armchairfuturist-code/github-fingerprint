# S04: Scoring-sp1-core Cross-Comparison Test

**Goal:** Create scoring-cross-compare comparison tool that feeds identical ScoreInput fixtures to both scoring-sp1-core and scoring-core, reports exact diffs per signal, then fix all 5 drift points in scoring-sp1-core so both engines produce identical outputs.
**Demo:** Verify scoring-sp1-core output matches scoring-core output on identical inputs — analogous to py-scoring-ref/compare.py but Rust-to-Rust

## Must-Haves

- 1. `cargo build -p scoring-cross-compare` compiles successfully. 2. `cargo build -p scoring-sp1-core` compiles after all fixes. 3. `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json` outputs ALL PASS with zero-diff across all 12 signals, overall_score, risk_flags, and metadata. 4. `cargo test` passes with no regressions.

## Proof Level

- This slice proves: integration

## Integration Closure

The cross-comparison crate proves that scoring-sp1-core and scoring-core produce identical outputs for the same inputs. This closes the risk of score divergence between attested (Ed25519) and proved (ZKP) scores. The comparison tool is standalone and does not need to be wired into any runtime pipeline — it is a one-time verification artifact.

## Verification

- The cross-comparison tool prints per-signal PASS/FAIL lines and exits non-zero on any diff. Output includes overall_score comparison, per-signal score/confidence/details comparison, risk_flags comparison, and metadata comparison. Executors can read the diff output to localize which signal drifted and by how much.

## Tasks

- [x] **T01: Create scoring-cross-compare crate** `est:1h`
  Create a new Rust binary crate `scoring-cross-compare` that feeds identical ScoreInput JSON fixtures to both scoring_core::engine::score_user and scoring_sp1_core::score_user, then compares every signal score + confidence + details + overall_score + risk_flags with zero tolerance (exact f64 equality). Add to workspace members.
  - Files: `scoring-cross-compare/Cargo.toml`, `scoring-cross-compare/src/main.rs`, `Cargo.toml`
  - Verify: cargo build -p scoring-cross-compare

- [x] **T02: Fix commit_semantics conventional commit detection and project_ownership signature** `est:30m`
  Fix two drift points in scoring-sp1-core/src/engine.rs:
  - Files: `scoring-sp1-core/src/engine.rs`
  - Verify: cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json

- [x] **T03: Add timing cluster analysis to ai_usage_patterns** `est:1h`
  Add the missing timing cluster analysis to `ai_usage_patterns()` in scoring-sp1-core/src/engine.rs. This is the largest drift point with up to 30 points score impact. **Requires sort** — use `Vec::sort_by_key` on commit date strings, or collect into a sorted Vec.
  - Files: `scoring-sp1-core/src/engine.rs`
  - Verify: cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json

- [x] **T04: Fix readme_quality — add emoji score and list_count** `est:30m`
  Fix two drift points in `readme_quality()` in scoring-sp1-core/src/engine.rs:
  - Files: `scoring-sp1-core/src/engine.rs`
  - Verify: cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json

- [x] **T05: Run cross-comparison and achieve zero-diff across all fixtures** `est:45m`
  Run the full cross-comparison against all available fixtures. Fix any remaining discrepancies that surface only on certain fixture configurations (e.g. edge cases with empty fields, fractional-second timestamps, or missing data).
  - Files: `py-scoring-ref/fixtures/empty_input.json`, `py-scoring-ref/fixtures/minimal_profile.json`
  - Verify: cargo run -p scoring-cross-compare -- --all-fixtures && cargo test

## Files Likely Touched

- scoring-cross-compare/Cargo.toml
- scoring-cross-compare/src/main.rs
- Cargo.toml
- scoring-sp1-core/src/engine.rs
- py-scoring-ref/fixtures/empty_input.json
- py-scoring-ref/fixtures/minimal_profile.json
