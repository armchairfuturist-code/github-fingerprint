---
estimated_steps: 16
estimated_files: 1
skills_used: []
---

# T03: Port all 12 signals to Rust

Port all 12 signals from Python signals/extractor.py to Rust scoring-signals crate:

1. commit_consistency — analyze commit frequency and patterns
2. language_diversity — count unique languages across repos
3. issue_engagement — analyze issue creation and participation
4. pr_patterns — analyze PR creation patterns
5. project_ownership — measure original vs forked repos
6. review_patterns — analyze review activity
7. response_time — time to first response on issues/PRs
8. readme_quality — README content quality analysis
9. commit_semantics — conventional commit parsing
10. cicd_maturity — CI/CD config detection
11. contribution_consistency — contribution calendar analysis
12. ai_usage_patterns — detect AI-generated contribution patterns

Each signal is a function: fn extract(context: &ScoreInput) -> SignalScore
Return SignalScore { signal_name, score: 0-100, confidence: 0-1, details: {...} }

Output: all 12 signals implemented. Tests produce scores for a sample ScoreInput.

## Inputs

- `signals/extractor.py (all signal logic)`

## Expected Output

- `scoring-signals/src/commit_consistency.rs`
- `scoring-signals/src/language_diversity.rs`
- `scoring-signals/src/issue_engagement.rs`
- `scoring-signals/src/pr_patterns.rs`
- `scoring-signals/src/project_ownership.rs`
- `scoring-signals/src/review_patterns.rs`
- `scoring-signals/src/response_time.rs`
- `scoring-signals/src/readme_quality.rs`
- `scoring-signals/src/commit_semantics.rs`
- `scoring-signals/src/cicd_maturity.rs`
- `scoring-signals/src/contribution_consistency.rs`
- `scoring-signals/src/ai_usage_patterns.rs`
- `scoring-signals/src/lib.rs`

## Verification

cargo test. Every signal produces valid output for a sample ScoreInput. Compare output against Python reference for the same input.
