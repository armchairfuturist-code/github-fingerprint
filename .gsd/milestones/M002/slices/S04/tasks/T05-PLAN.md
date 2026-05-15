---
estimated_steps: 9
estimated_files: 2
skills_used: []
---

# T05: Run cross-comparison and achieve zero-diff across all fixtures

Run the full cross-comparison against all available fixtures. Fix any remaining discrepancies that surface only on certain fixture configurations (e.g. edge cases with empty fields, fractional-second timestamps, or missing data).

1. Run `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json` — verify ALL PASS with zero-diff.
2. Create at least 2 additional edge-case fixtures:
   - `py-scoring-ref/fixtures/empty_input.json`: empty repos, empty commits, empty issues, empty PRs, empty readmes, empty cicd_configs, None contributions.
   - `py-scoring-ref/fixtures/minimal_profile.json`: minimal data with fractional-second timestamps, a single commit, no readmes, no CI/CD.
3. Run against all fixtures: `cargo run -p scoring-cross-compare -- --all-fixtures` — verify ALL PASS.
4. Run `cargo test` — verify all tests pass with no regressions.
5. If any diff is found, diagnose and fix the remaining drift point(s), then re-verify.

**Pure verification task — produces no new source files, only test fixture JSON files.**

## Inputs

- `scoring-cross-compare/src/main.rs`
- `scoring-sp1-core/src/engine.rs`
- `py-scoring-ref/fixtures/sample_profile.json`

## Expected Output

- `py-scoring-ref/fixtures/empty_input.json`
- `py-scoring-ref/fixtures/minimal_profile.json`

## Verification

cargo run -p scoring-cross-compare -- --all-fixtures && cargo test
