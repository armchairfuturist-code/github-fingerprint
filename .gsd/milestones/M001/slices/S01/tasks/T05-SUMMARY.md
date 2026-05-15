---
id: T05
parent: S01
milestone: M001
key_files:
  - signals/extractor.py
  - scoring/engine.py
  - tests/test_scoring.py
  - tests/test_crawler.py
key_decisions:
  - All 5 new signals integrated into extract_all_signals() alongside 8 original signals
  - ScoringEngine weights include all 13 signals with correct proportions summing to 1.0
  - Tests cover readme_quality, commit_semantics, cicd_maturity, contribution_consistency, ai_usage_patterns extractors
  - Crawl cache tests verify first-run, cache-hit skip, and stale-repo refresh paths
duration: 
verification_result: passed
completed_at: 2026-05-12T05:25:12.461Z
blocker_discovered: false
---

# T05: Integrated all 5 new signals into extract_all_signals(), updated ScoringEngine with proportional weights (sum=1.0), added comprehensive unit tests for all new signal extractors and crawler methods — all 69 tests pass.

**Integrated all 5 new signals into extract_all_signals(), updated ScoringEngine with proportional weights (sum=1.0), added comprehensive unit tests for all new signal extractors and crawler methods — all 69 tests pass.**

## What Happened

Task T05 verified the complete integration of the deep data pipeline and signal extraction system. Reviewed signals/extractor.py confirming extract_all_signals() wires all 5 new signals (readme_quality, commit_semantics, cicd_maturity, contribution_consistency, ai_usage_patterns) alongside the original 8. Verified ScoringEngine default weights include all 13 signals with correct proportional distribution summing to 1.0. Tests in test_scoring.py cover all new signal extractors with mock data (README text, commit messages, contribution calendar, CI/CD configs). Tests in test_crawler.py cover get_repo_readme, get_user_contributions, get_repo_cicd_configs methods with proper mocks. Crawl cache tests verify first-run caching, cache-hit skip behavior, and stale-repo refresh. Full test suite passes with 69/69 tests.

## Verification

python -m pytest tests/ -x -v — 69 passed in 0.07s

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/ -x -v` | 0 | ✅ pass | 70ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `signals/extractor.py`
- `scoring/engine.py`
- `tests/test_scoring.py`
- `tests/test_crawler.py`
