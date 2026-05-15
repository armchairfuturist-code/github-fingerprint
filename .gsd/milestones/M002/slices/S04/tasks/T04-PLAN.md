---
estimated_steps: 11
estimated_files: 1
skills_used: []
---

# T04: Fix readme_quality — add emoji score and list_count

Fix two drift points in `readme_quality()` in scoring-sp1-core/src/engine.rs:

**Drift 3 — emoji score:** Currently has `+ 0.0` with comment `// emoji skipped in SP1`. Replace with actual emoji score:
1. Add `let mut repos_with_emoji = 0i64;` to the accumulator variables
2. Inside the repo loop, add `if rm.has_emoji { repos_with_emoji += 1; }`
3. Compute `let emoji_score = (repos_with_emoji as f64 / rwr as f64) * 15.0;`
4. Replace `+ 0.0` with `+ (repos_with_emoji as f64 / rwr as f64) * 15.0`

**Drift 4 — list_count:** Currently missing from structure formula:
1. Add `let mut total_lists = 0i64;` to the accumulator variables
2. Inside the repo loop, add `total_lists += rm.list_count;`
3. Change structure formula from `(ts as f64 / rwr as f64 * 5.0 + tcb as f64 / rwr as f64 * 3.0).min(30.0)` to `(ts as f64 / rwr as f64 * 5.0 + tcb as f64 / rwr as f64 * 3.0 + total_lists as f64 / rwr as f64 * 1.5).min(30.0)`

Also add richer metadata to match scoring-core: include avg_char_count, avg_sections, avg_code_blocks, avg_lists, avg_badges, emoji_ratio in the details BTreeMap.

## Inputs

- `scoring-sp1-core/src/engine.rs`
- `scoring-core/src/engine.rs`

## Expected Output

- `scoring-sp1-core/src/engine.rs`

## Verification

cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json
