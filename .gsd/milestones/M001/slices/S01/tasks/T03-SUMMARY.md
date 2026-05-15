---
id: T03
parent: S01
milestone: M001
key_files:
  - signals/extractor.py
  - scoring/engine.py
  - tests/test_scoring.py
key_decisions:
  - README quality signal reads actual content from readmes dict when available, falls back to description scoring otherwise (mode field indicates which path)
  - Commit semantics signal imports CONVENTIONAL_COMMIT_RE regex from crawler.github_api to avoid duplication
  - Scoring weights redistributed: readme_quality stays at 0.10, commit_semantics added at 0.11, others scaled proportionally to maintain sum of 1.0
duration: 
verification_result: passed
completed_at: 2026-05-12T05:21:36.938Z
blocker_discovered: false
---

# T03: Added README content quality signal (analyzes actual README content for sections, code blocks, lists, badges, emoji) and commit message semantics signal (detects conventional commits, imperative mood, multi-line messages), wired into extract_all_signals and scoring engine

**Added README content quality signal (analyzes actual README content for sections, code blocks, lists, badges, emoji) and commit message semantics signal (detects conventional commits, imperative mood, multi-line messages), wired into extract_all_signals and scoring engine**

## What Happened

Implemented two new signal extractors in signals/extractor.py:

1. **extract_readme_quality** — upgraded from repo-description-only to analyze actual README content when available (via the readmes dict in activity_data). Scores based on: README presence ratio (0-30), structure from sections/code blocks/lists (0-30), richness from content length and badges (0-25), and polish from emoji usage (0-15). Falls back to description-only scoring when no README content is available, with a `mode` field in details indicating which scoring path was taken.

2. **extract_commit_semantics** — new signal analyzing commit messages for: conventional commit pattern ratio (feat:, fix:, docs:, etc.) worth 0-30 points; average message length (0-25); multi-line message ratio indicating body content (0-25); and imperative mood usage (first-word verb detection, 0-20). Includes a `conventional_breakdown` detail mapping conventional types to counts.

Both signals return 0-100 scores with confidence metrics scaling with data volume.

Updated `extract_all_signals` to pass the `readmes` dict to `extract_readme_quality` and include `commit_semantics` in the returned dict (total now 9 signals). Updated ScoringEngine default weights to include commit_semantics at 0.11 (other weights adjusted accordingly). Added 4 new tests in test_scoring.py covering both new signals.

## Verification

All 56 tests pass (46 existing + 10 scoring tests), including 4 new tests specifically verifying README content quality scoring, commit semantics scoring, positive scoring with README data, and commit semantics detail structure. Verified behavior with a smoke test showing both signals return valid 0-100 scores with confidence metrics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_scoring.py -x -v` | 0 | ✅ pass | 30ms |
| 2 | `python -m pytest tests/ -x -v` | 0 | ✅ pass | 60ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `signals/extractor.py`
- `scoring/engine.py`
- `tests/test_scoring.py`
