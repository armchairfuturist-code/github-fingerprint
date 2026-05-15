---
id: S04
parent: M002
milestone: M002
provides:
  - scoring-cross-compare crate — standalone verification tool
  - Zero-diff proof that scoring-sp1-core matches scoring-core for all 12 signals across 3 fixture configurations
requires:
  []
affects:
  []
key_files:
  - scoring-cross-compare/Cargo.toml
  - scoring-cross-compare/src/main.rs
  - Cargo.toml
  - scoring-sp1-core/src/engine.rs
key_decisions:
  - Used clap with derive for argument parsing (--fixture and --all-fixtures)
  - Exact f64 equality (==) for cross-comparison as specified in plan
  - Both engines called with role=None for apples-to-apples comparison
  - Applied exact-match CC detection pattern in both commit_semantics and ai_usage_patterns to prevent false prefix matches
  - Used date_parser::parse_timestamp() instead of chrono for sp1-core no_std compatibility
  - All scoring-sp1-core detail messages must match scoring-core exactly using exact string equality
patterns_established:
  - Cross-comparison crate pattern for verifying ZK-engine fidelity to reference engine
  - Per-signal exact-match verification as CI gate for scoring divergences
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-12T09:39:25.585Z
blocker_discovered: false
---

# S04: Scoring-sp1-core Cross-Comparison Test

**Created scoring-cross-compare crate and fixed 7 signal drift points in scoring-sp1-core to produce identical outputs to scoring-core across all 3 fixtures, achieving zero-diff cross-comparison.**

## What Happened

This slice built a Rust-to-Rust cross-comparison verification tool analogous to the Python py-scoring-ref/compare.py, then fixed all signal drift between scoring-sp1-core (ZK proving engine) and scoring-core (reference engine).

T01 created the scoring-cross-compare binary crate that feeds identical ScoreInput JSON fixtures to both scoring_core::engine::score_user and scoring_sp1_core::score_user, then compares every signal score + confidence + details + overall_score + risk_flags with exact f64 equality. Supports --fixture and --all-fixtures flags.

T02 fixed commit_semantics conventional commit detection from prefix-matching to exact-match pattern, enriched metadata with avg_message_length, multi_line_ratio, imperative_mood_ratio, and updated project_ownership signature to accept PR data parameter.

T03 added timing cluster analysis to ai_usage_patterns, replacing a hardcoded 25.0 score with computed timing_score and avg_msg_length metadata, using date_parser::parse_timestamp() for no_std SP1 compatibility.

T04 fixed readme_quality emoji score and list_count drift using inline formulas matching scoring-core's logic exactly.

T05 fixed 7 remaining signal drift points: cicd_maturity details, commit_consistency details, contribution_consistency message, issue_engagement details, language_diversity, pr_patterns details, and review_patterns details — achieving zero-diff across all 3 fixtures (sample_profile.json, empty_input.json, minimal_profile.json).

## Verification

1. cargo build -p scoring-cross-compare — compiles successfully (no warnings)
2. cargo build -p scoring-sp1-core — compiles after all fixes
3. cargo run -p scoring-cross-compare -- --all-fixtures — ALL 3 fixtures PASS with zero-diff (exit 0). Per-signal comparison includes overall_score, score/confidence/details, risk_flags, and signals_below_threshold for all 12 signals.
4. cargo test — all 8 crates pass, 0 failures
5. py -m pytest — 286 Python tests pass

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None. All tasks completed as planned.

## Known Limitations

Running `pytest` bare command fails with ModuleNotFoundError because the project root is not on sys.path. Use `py -m pytest` instead (286 tests pass). A root-level conftest.py would fix this, but it's a pre-existing project setup gap.

## Follow-ups

None.

## Files Created/Modified

None.
