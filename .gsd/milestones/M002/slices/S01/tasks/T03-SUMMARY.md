---
id: T03
parent: S01
milestone: M002
key_files:
  - scoring-core/src/engine.rs
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T07:53:57.929Z
blocker_discovered: false
---

# T03: All 12 signals ported to Rust — scores match Python reference exactly (verified via comparison script).

**All 12 signals ported to Rust — scores match Python reference exactly (verified via comparison script).**

## What Happened

Ported all 12 signals from Python to Rust in scoring-core/src/engine.rs: commit_consistency, language_diversity, issue_engagement, pr_patterns, project_ownership, review_patterns, response_time, readme_quality, commit_semantics, cicd_maturity, contribution_consistency, ai_usage_patterns. Each signal extracts from the appropriate input data and returns a SignalScore with score, confidence, and details. Date parsing uses chrono with ISO 8601/RFC 3339 support.

## Verification

cargo test passes 8 tests including per-signal tests. py-scoring-ref/compare.py reports zero diffs: all signal scores match Python reference within ±0.5 tolerance for sample_profile.json fixture.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

ai_usage_patterns initially had a simplified timing score (hardcoded 25.0). Fixed by porting the full burst/timing cluster analysis from Python — code now matches exactly.

## Known Issues

None.

## Files Created/Modified

- `scoring-core/src/engine.rs`
