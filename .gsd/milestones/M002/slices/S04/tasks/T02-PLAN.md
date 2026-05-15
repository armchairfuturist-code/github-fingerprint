---
estimated_steps: 13
estimated_files: 1
skills_used: []
---

# T02: Fix commit_semantics conventional commit detection and project_ownership signature

Fix two drift points in scoring-sp1-core/src/engine.rs:

**Drift 1 — commit_semantics:** Change `if let Some(pos) = c.message.find(':') { if cc.iter().any(|t| c.message[..pos].starts_with(t)) { ccnt += 1; } }` 
to use the same exact-match pattern as scoring-core:
```rust
if let Some(pos) = c.message.find(':') {
    let prefix = &c.message[..pos];
    if cc.iter().any(|t| prefix == *t || prefix == &alloc::format!("{}!", t) || prefix.starts_with(&alloc::format!("{}(", t))) { ccnt += 1; }
}
```
This prevents false matches like `"feature: ..."` matching the `feat` token.

**Drift same pattern in ai_usage_patterns:** Change the same starts_with pattern at the conventional commit detection inside `ai_usage_patterns()` to use the exact-match pattern too.

**Drift 5 — project_ownership:** Change signature from `fn project_ownership(repos: &[scoring_types::RepoData])` to `fn project_ownership(repos: &[scoring_types::RepoData], _prs: &[scoring_types::PrData])` to match scoring-core's `extract_project_ownership(repos, _prs)`. Update the caller in `extract_all_signals` to pass `&input.prs`.

**Important:** The `extract_all_signals()` function in sp1-core maps signals differently (no `extract_` prefix). Update the caller line `r.insert("project_ownership".into(), project_ownership(&input.repos));` to pass `&input.prs` as second argument. Also update the `avg_msg_length` and `conventional_commit_ratio` metadata details for `commit_semantics` to match scoring-core's richer metadata.

## Inputs

- `scoring-sp1-core/src/engine.rs`
- `scoring-core/src/engine.rs`

## Expected Output

- `scoring-sp1-core/src/engine.rs`

## Verification

cargo build -p scoring-sp1-core && cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json
