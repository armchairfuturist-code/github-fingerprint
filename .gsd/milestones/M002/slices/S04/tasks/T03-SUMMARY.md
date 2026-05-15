---
id: T03
parent: S04
milestone: M002
key_files:
  - scoring-sp1-core/src/engine.rs
key_decisions:
  - Used date_parser::parse_timestamp() instead of chrono for sp1-core no_std compatibility
  - Annotated timing_score: f64 explicitly to resolve Rust numeric type inference in conditional return
  - Burst cluster counting matches scoring-core: counts total commits in clusters >3, not just cluster count
duration: 
verification_result: passed
completed_at: 2026-05-12T09:30:42.189Z
blocker_discovered: false
---

# T03: Added timing cluster analysis to ai_usage_patterns in scoring-sp1-core, replacing hardcoded 25.0 with computed timing_score and adding avg_msg_length metadata, achieving exact match with scoring-core for ai_usage_patterns signal

**Added timing cluster analysis to ai_usage_patterns in scoring-sp1-core, replacing hardcoded 25.0 with computed timing_score and adding avg_msg_length metadata, achieving exact match with scoring-core for ai_usage_patterns signal**

## What Happened

Implemented the timing cluster analysis in ai_usage_patterns() in scoring-sp1-core/src/engine.rs, matching the scoring-core reference implementation (lines 528-566). The implementation: (1) sorts commits by date using Vec::sort_by_key, (2) computes time diffs between consecutive commits using date_parser::parse_timestamp() (sp1-core's no_std-compatible alternative to chrono), (3) detects burst clusters where diffs < 60s, counting clusters > 3 commits as burst commits, (4) computes burst_ratio = burst_commits / total_commits and applies the scoring thresholds (5.0 for br>0.5, 20.0 for br>0.3, 35.0 for br<0.1 && avg_diff>3600s, 30.0 for br<0.2, 25.0 default), (5) handles <2 commits edge case with timing_score=20.0, and (6) enriched metadata with avg_msg_length and msg_length_std. The hardcoded 25.0_f64 was replaced with the computed timing_score.

## Verification

cargo build -p scoring-sp1-core succeeds. cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json shows PASS for ai_usage_patterns signal with exact equality. cargo test passes with all 8 tests passing in scoring-core and no regressions elsewhere.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cargo build -p scoring-sp1-core` | 0 | ✅ pass | 240ms |
| 2 | `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json (ai_usage_patterns)` | 0 | ✅ pass — ai_usage_patterns matches exactly | 600ms |
| 3 | `cargo test` | 0 | ✅ pass — all 8 tests pass | 650ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1-core/src/engine.rs`
