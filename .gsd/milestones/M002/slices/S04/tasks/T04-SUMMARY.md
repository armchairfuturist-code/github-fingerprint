---
id: T04
parent: S04
milestone: M002
key_files:
  - scoring-sp1-core/src/engine.rs
key_decisions:
  - Inline formula matching scoring-core for emoji_score and list_count; using same rounding for metadata (10.0 multiplier round to 1 decimal)
duration: 
verification_result: untested
completed_at: 2026-05-12T09:32:16.539Z
blocker_discovered: false
---

# T04: Fixed readme_quality emoji score and list_count drift in scoring-sp1-core, matching scoring-core output exactly

**Fixed readme_quality emoji score and list_count drift in scoring-sp1-core, matching scoring-core output exactly**

## What Happened

Fixed two drift points in readme_quality() in scoring-sp1-core/src/engine.rs: (1) Emoji score — replaced the hardcoded `+ 0.0` with actual `repos_with_emoji` accumulation and computed `(repos_with_emoji as f64 / rwr as f64) * 15.0`. (2) List count — added `total_lists` accumulator with `rm.list_count` inside the repo loop, and included it in the structure formula as `+ total_lists as f64 / rwr as f64 * 1.5`. Also enriched the details BTreeMap with avg_char_count, avg_sections, avg_code_blocks, avg_lists, avg_badges, and emoji_ratio to match scoring-core metadata.

## Verification

cargo build -p scoring-sp1-core passes. cargo run -p scoring-cross-compare -- --all-fixtures shows readme_quality PASS on all fixtures. Other failures are pre-existing diffs outside T04 scope (cicd_maturity details, commit_consistency details, contribution_consistency message, issue_engagement details, language_diversity, pr_patterns details, review_patterns details).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1-core/src/engine.rs`
