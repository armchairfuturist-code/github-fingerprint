---
estimated_steps: 14
estimated_files: 1
skills_used: []
---

# T03: Add timing cluster analysis to ai_usage_patterns

Add the missing timing cluster analysis to `ai_usage_patterns()` in scoring-sp1-core/src/engine.rs. This is the largest drift point with up to 30 points score impact. **Requires sort** — use `Vec::sort_by_key` on commit date strings, or collect into a sorted Vec.

Implementation (match scoring-core lines 528-566):
1. Sort commits by date: `let mut sorted: Vec<_> = commits.iter().collect(); sorted.sort_by_key(|c| &c.date);`
2. Compute time diffs: iterate from 1..sorted.len(), use `date_parser::parse_timestamp()` to get i64 values, compute difference in seconds as f64
3. Detect burst clusters: iterate diffs, cluster when `< 60.0` seconds. If cluster > 3, count as burst. Track `burst_clusters` count and compute `br = burst_clusters as f64 / n`.
4. Calculate timing_score:
   - `br > 0.5` → 5.0
   - `br > 0.3` → 20.0
   - `br < 0.1 && avg_diff > 3600.0` → 35.0
   - `br < 0.2` → 30.0
   - default → 25.0
5. Replace `style + 25.0_f64 + ccs` with `style + timing_score + ccs`
6. Handle edge case: if fewer than 2 commits, timing_score = 20.0
7. Add `"avg_msg_length"` to metadata (missing in sp1-core's ai_usage_patterns metadata).

## Inputs

- `scoring-sp1-core/src/engine.rs`
- `scoring-core/src/engine.rs`

## Expected Output

- `scoring-sp1-core/src/engine.rs`

## Verification

cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json
