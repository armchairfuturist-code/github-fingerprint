---
id: T02
parent: S04
milestone: M002
key_files:
  - scoring-sp1-core/src/engine.rs
key_decisions:
  - Applied exact-match CC detection pattern in both commit_semantics and ai_usage_patterns to prevent false prefix matches
  - Exposed avg_message_length, multi_line_ratio, imperative_mood_ratio in commit_semantics metadata
  - Added _prs parameter to project_ownership with leading underscore to match scoring-core's unused parameter pattern
duration: 
verification_result: passed
completed_at: 2026-05-12T09:28:11.866Z
blocker_discovered: false
---

# T02: Fixed commit_semantics conventional commit detection to use exact-match pattern, enriched commit_semantics metadata, and updated project_ownership signature to accept PR data parameter in scoring-sp1-core

**Fixed commit_semantics conventional commit detection to use exact-match pattern, enriched commit_semantics metadata, and updated project_ownership signature to accept PR data parameter in scoring-sp1-core**

## What Happened

Applied 5 targeted fixes to scoring-sp1-core/src/engine.rs to eliminate drift between scoring-sp1-core and scoring-core:

1. **commit_semantics CC detection** (Drift 1): Changed `starts_with(t)` to exact-match pattern `prefix == *t || prefix == format!("{}!", t) || prefix.starts_with(format!("{}(", t))` to prevent false matches like "feature:" matching "feat".

2. **commit_semantics metadata enrichment**: Added `avg_message_length`, `multi_line_ratio`, and `imperative_mood_ratio` to the details map to match scoring-core's richer metadata output. The variables `ar`, `mr`, `ir` were already computed but not exposed.

3. **ai_usage_patterns CC detection**: Applied the same exact-match pattern fix to the conventional commit detection in `ai_usage_patterns()`.

4. **project_ownership signature** (Drift 5): Changed from `fn project_ownership(repos)` to `fn project_ownership(repos, _prs)` to match scoring-core's `extract_project_ownership(repos, _prs)`.

5. **Caller update in extract_all_signals**: Updated `r.insert("project_ownership", project_ownership(&input.repos))` to pass `&input.prs` as second argument.

Cross-compare confirmed: commit_semantics went from FAIL to PASS, project_ownership remained PASS. Remaining FAILs are from other signals outside T02's scope.

## Verification

cargo build -p scoring-sp1-core succeeded with no errors. cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json confirmed commit_semantics changed from FAIL to PASS and project_ownership remained PASS.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cargo build -p scoring-sp1-core` | 0 | ✅ pass | 240ms |
| 2 | `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json` | 1 | ⚠️ partial — T02 signals pass; remaining failures are other signals | 580ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1-core/src/engine.rs`
