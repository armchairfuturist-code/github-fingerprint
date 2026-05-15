# S04: Scoring-sp1-core Cross-Comparison Test — Research

**Date:** 2026-05-12

## Summary

**scoring-sp1-core (no_std) has 5 confirmed drift points vs scoring-core (std), 4 of which are actual bugs that will produce different scores and 1 that is a deliberate omission.** The comparison test infrastructure needs to be a standalone Rust binary (new `scoring-cross-compare` crate) that feeds identical ScoreInput fixtures to both engines, compares every signal score + confidence + metadata + overall score, and fails on any non-zero divergence (zero tolerance, unlike the py compare's 0.5 tolerance).

The identified divergences range from **minor** (1.5-point list_score gap in readme_quality) to **significant** (missing timing cluster analysis in ai_usage_patterns — can shift score by up to 30 points; overly broad conventional commit detection in commit_semantics — shifts score by up to 30 points; missing 15-point emoji component in readme_quality). Immediate next step after building the comparison tool is to patch scoring-sp1-core to match scoring-core exactly, then confirm zero-diff.

## Recommendation

1. **Create `scoring-cross-compare/`** — a new Rust binary crate in the root workspace that depends on both `scoring-core` and `scoring-sp1-core`, reads ScoreInput JSON fixtures, runs both engines, and reports exact diffs.
2. **Run on existing fixture** (`py-scoring-ref/fixtures/sample_profile.json`) — this will confirm the absolute magnitude of drift.
3. **Fix scoring-sp1-core to match scoring-core** in all 5 drift areas.
4. **Add more edge-case fixtures** (empty inputs, null fields, fractional-second timestamps, edge weights).
5. **Verify zero-diff** across all fixtures before marking slice complete.

## Implementation Landscape

### Key Files

- **`scoring-core/src/engine.rs`** — Reference std implementation. All 12 signal extractors are in this file plus inline tests.
- **`scoring-sp1-core/src/engine.rs`** — no_std reimplementation. Functions named without `extract_` prefix (e.g. `commit_consistency()` vs `extract_commit_consistency()`). Contains 5 confirmed drift points (see below).
- **`scoring-core/src/profiles.rs`** — std role profiles. Should be byte-identical result to `scoring-sp1-core/src/profiles.rs` (verified — same weights, thresholds, profiles).
- **`scoring-sp1-core/src/date_parser.rs`** — Custom no_std ISO 8601 parser. Returns integer seconds from Unix epoch. Must be verified against chrono output on edge cases (fractional seconds, timezone offsets).
- **`py-scoring-ref/fixtures/sample_profile.json`** — Existing ScoreInput fixture. Reusable for Rust-to-Rust comparison.
- **`scoring-cli/src/main.rs`** — Existing CLI for `scoring-core`. Pattern for reading ScoreInput JSON from file.
- **`py-scoring-ref/compare.py`** — Python-vs-Rust comparison script. Structural pattern to follow but Rust-to-Rust should use zero tolerance, not 0.5.

### New File: `scoring-cross-compare/Cargo.toml`

```toml
[package]
name = "scoring-cross-compare"
version = "0.1.0"
edition = "2021"

[dependencies]
scoring-types = { path = "../scoring-types" }
scoring-core = { path = "../scoring-core" }
scoring-sp1-core = { path = "../scoring-sp1-core" }
serde_json = "1"
```

### New File: `scoring-cross-compare/src/main.rs`

Rust binary that:
1. Takes `--fixture <path>` (single fixture) or `--all-fixtures` (default path `py-scoring-ref/fixtures/`)
2. Reads fixture JSON into `ScoreInput`
3. Calls `scoring_core::engine::score_user(&input, None)` for reference result
4. Calls `scoring_sp1_core::score_user(&input, None)` for test result
5. Compares: overall_score (exact f64), each signal name/score/confidence (exact f64), metadata keys presence, risk_flags
6. Prints structured diff or PASS
7. Exits 0 if all pass, 1 if any diff

### Build Order

1. Create `scoring-cross-compare/` with `Cargo.toml` and `src/main.rs`
2. Add `"scoring-cross-compare"` to workspace members in root `Cargo.toml`
3. `cargo build -p scoring-cross-compare` — verify it compiles
4. `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json` — first comparison run
5. Fix identified drift in `scoring-sp1-core/src/engine.rs`
6. Create additional edge-case fixtures
7. Re-run until zero-diff across all fixtures
8. `cargo test` — verify no regressions

### Verification Approach

```bash
# Build and run comparison on single fixture
cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json

# After fixes, run on all fixtures
cargo run -p scoring-cross-compare -- --all-fixtures
# Expected: All PASS (zero-diff)

# Verify no regressions to existing Rust tests
cargo test
# Expected: All passing
```

## Confirmed Drift: scoring-sp1-core vs scoring-core

### Drift 1 — `commit_semantics`: Overly broad conventional commit detection (BUG)

**File:** `scoring-sp1-core/src/engine.rs`, `commit_semantics()` function  
**scoring-core:** `prefix == *t || prefix == &format!("{}!", t) || prefix.starts_with(&format!("{}(", t))` — exact match or with `!` or `(scope)` suffix  
**scoring-sp1-core:** `c.message[..pos].starts_with(t)` — substring match at prefix position  

**Impact:** "feature: add X" falsely matches "feat" conventional type because `"feature".starts_with("feat")` is true. This inflates the conventional commit count. Score impact: up to +30 points (`cr * 30.0` component).

### Drift 2 — `ai_usage_patterns`: Missing timing cluster analysis (BUG)

**File:** `scoring-sp1-core/src/engine.rs`, `ai_usage_patterns()` — lines 524-566 in core, entirely absent in sp1-core  
**scoring-core:** Has full timing cluster analysis: burst detection (commits < 60s apart → burst cluster), timing_score calculation (5-35 points based on burst_ratio), contributes to final ai_score  
**scoring-sp1-core:** Only has style_score + 25.0 + cc_score. No timing/burst detection at all. The extra 25.0 constant replaces the entire timing analysis.

**Impact:** For bursty committers, ai_usage_patterns score can differ by ~30 points. The 25.0 constant in SP1 always contributes 25, whereas scoring-core's timing_score varies from 5 (high burst) to 35 (low burst + sparse timing).

### Drift 3 — `readme_quality`: Missing emoji score (DELIBERATE OMISSION)

**File:** `scoring-sp1-core/src/engine.rs`, `readme_quality()` — comment says "emoji skipped in SP1"  
**scoring-core:** `let emoji_score = (repos_with_emoji as f64 / rwr) * 15.0;` — contributes up to 15 points  
**scoring-sp1-core:** Has `+ 0.0)` in the quality formula instead of `+ emoji_score`

**Impact:** When readmes contain emoji, SP1 score is 0-15 points lower. Decision: fix to match or document as intentional.

### Drift 4 — `readme_quality`: Missing list count in structure component (BUG)

**File:** `scoring-sp1-core/src/engine.rs`, `readme_quality()`  
**scoring-core:** `structure = (sections * 5.0 + code_blocks * 3.0 + lists * 1.5).min(30.0)` — includes list_count  
**scoring-sp1-core:** `structure = (sections * 5.0 + code_blocks * 3.0).min(30.0)` — no list term

**Impact:** Max score gap: 1.5 points when readmes have lists. Minor but real.

### Drift 5 — `project_ownership`: Signature accepts PRs but ignores them (COSMETIC)

**scoring-core:** `fn extract_project_ownership(repos, _prs)` — underscore prefix explicitly ignores  
**scoring-sp1-core:** `fn project_ownership(repos)` — doesn't take PRs at all  

**Impact:** No score drift (both ignore PRs). But the different signature is a maintenance hazard — if core ever uses the PR parameter, SP1 won't automatically adapt.

### No Drift Confirmed

- **Profiles** — `profiles.rs` in both crates produce identical RoleProfiles (same weights, thresholds, profile names)
- **`language_diversity`** — same entropy formula, same max_entropy normalization
- **`issue_engagement`** — same formula: `(avg_comments * 20.0 + close_rate * 50.0).min(100.0)`
- **`pr_patterns`** — identical formula
- **`review_patterns`** — identical
- **`response_time`** — identical formula
- **`cicd_maturity`** — same logic
- **`contribution_consistency`** — same score/confidence formula (metadata differs in extra fields but that's cosmetic)
- **`filter_by_confidence` + `calculate_overall_score` pipeline** — identical in both
- **`generate_risk_flags`** — identical

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| JSON comparison of f64 values | `serde_json::to_value` + value comparison | Both engines already output serde-serializable ScoreOutput; compare the serialized forms |
| Fixture management | Reuse existing `py-scoring-ref/fixtures/` | Same fixtures already work for Python-vs-Rust comparison; no need for new format |

## Common Pitfalls

- **f64 comparison** — The `ScoreOutput` fields are `f64`. Cross-comparison should use exact equality (`==`) rather than epsilon-based tolerance, because if the same formula produces different floats, that's a bug. Use `format!("{:.10}", v)` string comparison if NaN/subnormal concerns arise.
- **BTreeMap key ordering** — Both engines use `BTreeMap` for `signal_scores`, so iteration order is deterministic. Compare key-by-key, not by JSON string.
- **Role default** — Both engines use engineering profile when `role: None` is passed. Verify this in the comparison binary.
- **Date parsing edge cases** — scoring-core's `parse_dt()` tries rfc3339 → fractional seconds → plain ISO8601; scoring-sp1-core's `parse_timestamp()` only handles `"2024-01-01T10:00:00Z"` and `"2024-01-01T10:00:00.123Z"` (fractional seconds stripped). If a fixture has fractional seconds, both will parse but should produce the same integer-second result.

## Open Risks

- The `scoring-sp1-core` no_std environment can't use `std::collections::BTreeMap` — it uses `alloc::collections::BTreeMap`. The cross-compare binary is a std binary and links `scoring-sp1-core` in std-compatible mode (alloc is available). This should compile fine since scoring-sp1-core's `Cargo.toml` doesn't set `no_std` behavior in a way that prevents std linking — the `#![no_std]` is only in `scoring-sp1/program/src/main.rs` (the guest binary), not in `scoring-sp1-core/src/lib.rs`. Confirmed: `scoring-sp1-core/src/lib.rs` has no `#![no_std]` attribute, only `#![cfg_attr(not(feature = "std"), no_std)]` in `scoring-types`. So linking into a std binary is fine.

## Sources

- The 5 drift points are identified from direct file-level comparison of `scoring-core/src/engine.rs` vs `scoring-sp1-core/src/engine.rs` and `scoring-core/src/engine.rs` vs `scoring-sp1-core/src/engine.rs`.
- The existing cross-comparison pattern is from `py-scoring-ref/compare.py` (Python-vs-Rust with 0.5 tolerance).
- The memory store confirms this gap: MEM068 says "scoring-sp1-core reimplements the 12 signal extractors... without a cross-comparison test."
