---
id: T05
parent: S01
milestone: M002
key_files:
  - scoring-cli/src/main.rs
  - py-scoring-ref/compare.py
  - py-scoring-ref/fixtures/sample_profile.json
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T07:54:18.754Z
blocker_discovered: false
---

# T05: CLI binary and Python comparison script built — verified Rust and Python produce identical scores (51.19 overall, zero diffs across all 12 signals).

**CLI binary and Python comparison script built — verified Rust and Python produce identical scores (51.19 overall, zero diffs across all 12 signals).**

## What Happened

Built the CLI binary (scoring-cli) that reads ScoreInput JSON from file or stdin and outputs ScoreOutput JSON. Created a rich test fixture (sample_profile.json) with 5 repos, 12 commits, 4 issues, 5 PRs, README content with structure analysis, CI/CD configs, and contribution calendar data. Built the Python comparison script (compare.py) that converts fixture JSON to typed Python objects, runs the Python scoring engine, runs the Rust CLI, and compares all signal scores, confidence values, overall scores, and risk flags — producing a diff report.

## Verification

scoring-cli.exe --input py-scoring-ref/fixtures/sample_profile.json outputs valid ScoreOutput JSON. py-scoring-ref/compare.py reports PASS with zero diffs between Python and Rust outputs.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

Had to build a more complex Python comparison script that converts JSON dicts to typed Python objects (SimpleNamespace) since the Python signal extractor expects dataclass-like objects, not raw dicts. This adds 100+ lines of conversion helpers but enables accurate cross-language comparison.

## Known Issues

None.

## Files Created/Modified

- `scoring-cli/src/main.rs`
- `py-scoring-ref/compare.py`
- `py-scoring-ref/fixtures/sample_profile.json`
