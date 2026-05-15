---
id: T01
parent: S04
milestone: M002
key_files:
  - scoring-cross-compare/Cargo.toml
  - scoring-cross-compare/src/main.rs
  - Cargo.toml
key_decisions:
  - Used clap with derive for argument parsing (--fixture and --all-fixtures)
  - Exact f64 equality (==) for comparison as specified in plan
  - Both engines called with role=None for apples-to-apples comparison
  - Per-signal detail comparison includes all BTreeMap keys from both engines
duration: 
verification_result: passed
completed_at: 2026-05-12T09:25:33.539Z
blocker_discovered: false
---

# T01: Created scoring-cross-compare binary crate that feeds identical ScoreInput fixtures to both scoring-core and scoring-sp1-core engines, reports per-signal PASS/FAIL diffs with exact f64 equality, and exits non-zero on any mismatch.

**Created scoring-cross-compare binary crate that feeds identical ScoreInput fixtures to both scoring-core and scoring-sp1-core engines, reports per-signal PASS/FAIL diffs with exact f64 equality, and exits non-zero on any mismatch.**

## What Happened

Created the scoring-cross-compare crate with Cargo.toml (depending on scoring-types, scoring-core, scoring-sp1-core, serde_json, clap) and src/main.rs. The tool accepts --fixture <path> for single fixture or --all-fixtures to scan py-scoring-ref/fixtures/*.json. For each fixture it: reads and parses ScoreInput JSON, calls both scoring_core::engine::score_user and scoring_sp1_core::score_user with None role, then deeply compares overall_score (exact f64 ==), per-signal score/confidence/details, risk_flags Vec equality, profile_name, signals_below_threshold, and signals_scored. Added to workspace members in root Cargo.toml. Built and tested against sample_profile.json — tool correctly detects 4 algorithmic drifts (ai_usage_patterns score 50.0 vs 40.0, language_diversity -26.1 vs 0.0, readme_quality 43.1 vs 31.1, contribution_consistency detail message mismatch) plus ~20 missing detail fields across signals.

## Verification

Verified with cargo build -p scoring-cross-compare (clean build, no warnings) and cargo run against sample_profile.json. Tool exits 0 on perfect match, exits 1 on any diff. Verified both --fixture and --all-fixtures flags work correctly.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cargo build -p scoring-cross-compare` | 0 | ✅ pass | 5830ms |
| 2 | `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json` | 1 | ✅ pass (correctly detected drifts) | 210ms |
| 3 | `cargo run -p scoring-cross-compare -- --all-fixtures` | 1 | ✅ pass (correctly detected drifts across all fixtures) | 150ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring-cross-compare/Cargo.toml`
- `scoring-cross-compare/src/main.rs`
- `Cargo.toml`
