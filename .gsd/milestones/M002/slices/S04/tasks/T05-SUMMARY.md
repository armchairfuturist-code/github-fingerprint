---
id: T05
parent: S04
milestone: M002
key_files:
  - scoring-sp1-core/src/engine.rs
  - py-scoring-ref/fixtures/empty_input.json
  - py-scoring-ref/fixtures/minimal_profile.json
key_decisions:
  - All scoring-sp1-core detail messages must match scoring-core exactly using exact string equality
  - Detail key names and computed values must match scoring-core exactly for cross-comparison to pass
duration: 
verification_result: passed
completed_at: 2026-05-12T09:36:21.639Z
blocker_discovered: false
---

# T05: Achieved zero-diff cross-comparison across all 3 fixtures and fixed 7 signal drift points in scoring-sp1-core to match scoring-core exactly

**Achieved zero-diff cross-comparison across all 3 fixtures and fixed 7 signal drift points in scoring-sp1-core to match scoring-core exactly**

## What Happened

Ran the scoring-cross-compare tool against the sample_profile.json fixture and discovered 7 signals with detail/score mismatches between scoring-core and scoring-sp1-core. Fixed all drift points in scoring-sp1-core/src/engine.rs:

1. **commit_consistency**: Added missing `std_dev_hours` detail key
2. **language_diversity**: Removed `.max(0.0)` clamp to allow negative entropy scores (matching reference), added `top_languages` detail
3. **issue_engagement**: Added missing `avg_comments_per_issue` and `close_rate` detail keys
4. **pr_patterns**: Added missing `avg_additions`, `avg_deletions`, `avg_files_changed` detail keys
5. **review_patterns**: Added missing `total_prs` and `avg_comments_per_pr` detail keys
6. **cicd_maturity**: Added missing `total_repos` and `ci_types_found` detail keys
7. **contribution_consistency**: Fixed empty message from "Empty calendar" to "Empty contribution calendar"
8. **Various messages**: Fixed 8 message strings across commit_semantics, ai_usage_patterns, response_time, readme_quality, project_ownership, and contribution_consistency to match scoring-core exactly
9. **readme_quality fallback**: Added missing `avg_description_length` detail key
10. **contribution_consistency fallback**: Added missing `mode: "commit_fallback"` detail key

Created 2 edge-case fixtures: empty_input.json (all empty/null) and minimal_profile.json (single commit with fractional-second timestamp, no readmes, no CI/CD).

Verified all 3 fixtures PASS with zero-diff via `cargo run -p scoring-cross-compare -- --all-fixtures`. All existing tests pass (8/8 in scoring-core, 0 failures across all 5 crates).

## Verification

cargo run -p scoring-cross-compare -- --all-fixtures — all 3 fixtures PASS with zero-diff (exit 0). cargo test — all 8 tests pass, 0 failures across all 5 crates.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cargo run -p scoring-cross-compare -- --all-fixtures` | 0 | ✅ pass | 570ms |
| 2 | `cargo test` | 0 | ✅ pass | 220ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1-core/src/engine.rs`
- `py-scoring-ref/fixtures/empty_input.json`
- `py-scoring-ref/fixtures/minimal_profile.json`
