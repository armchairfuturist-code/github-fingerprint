---
id: T04
parent: S01
milestone: M001
key_files:
  - signals/extractor.py
  - scoring/engine.py
  - tests/test_scoring.py
key_decisions:
  - CI/CD maturity uses type-based scoring with three sub-scores (prevalence, diversity, depth)
  - Contribution consistency uses contribution calendar days as primary source with commit-timing fallback
  - AI usage patterns scores organic patterns higher (60+), uniform bursts lower (<30), neutral at 50 with no data
duration: 
verification_result: passed
completed_at: 2026-05-12T05:24:40.234Z
blocker_discovered: false
---

# T04: Added 3 new signal extractors (CI/CD maturity, contribution graph consistency, AI usage patterns) to signals/extractor.py, wired into extract_all_signals, added default weights in scoring engine, and 15 new tests — all 69 tests pass.

**Added 3 new signal extractors (CI/CD maturity, contribution graph consistency, AI usage patterns) to signals/extractor.py, wired into extract_all_signals, added default weights in scoring engine, and 15 new tests — all 69 tests pass.**

## What Happened

Implemented the three signal extractors specified in the task plan:

1. **CI/CD maturity** (`extract_cicd_maturity`): Scores based on number and variety of CI/CD configs detected across repos. GitHub Actions = 20pts, other CI systems (CircleCI, Travis, Jenkins, etc.) = 15pts each, Dockerfile = 10pts. Three sub-scores: prevalence (0-30, fraction of repos with CI), diversity (0-30, number of distinct CI types), and depth (0-40, weighted per-type). Returns 0-100 with confidence based on CI adoption ratio.

2. **Contribution graph consistency** (`extract_contribution_consistency`): Analyzes contribution calendar data (GitHubContributionData.contribution_days) for regular vs bursty patterns. Three sub-scores: activity ratio (0-35), gap penalty for 30+ day inactivity windows (0-35), and weekly consistency via coefficient of variation across weeks (0-30). Falls back to commit-timing analysis when no calendar data is available — uses commit density and max gaps between commit dates.

3. **AI usage patterns** (`extract_ai_usage_patterns`): Analyzes commit message style uniformity (std-dev of message length), timing cluster analysis (burst detection for commits within 60s windows), and conventional commit consistency. Organic patterns with moderate variance score 60+, highly uniform bursts with very consistent conventional commit ratios score low (<30). Returns neutral 50 score when no data available.

All three wired into `extract_all_signals` passing `cicd_configs` and `contributions` from `activity_data`. Updated scoring engine default weights (12 signals now totalling weight 1.0, redistributed from the previous 9). Added 15 comprehensive tests covering empty data edge cases, expected scoring behavior, and comparative tests (more types = higher CI/CD score, regular vs sporadic contributions, organic vs suspicious AI patterns).

## Verification

All 69 tests pass across the full test suite (test_scoring.py + test_crawler.py). Specifically verified: CI/CD maturity returns 0 for no data, scores above 0 with configs, and multi-type > single-type. Contribution consistency returns 0 for no data, regular daily pattern >50, sporadic with 30+ day gap <50, and commit fallback mode works. AI usage organic pattern >=50, uniform burst <50, and details include all expected keys.

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
