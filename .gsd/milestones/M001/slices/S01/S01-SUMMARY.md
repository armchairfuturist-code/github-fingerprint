---
id: S01
parent: M001
milestone: M001
provides:
  - Deep pipeline activity_data keys: readmes, cicd_configs, contributions
  - 5 new SignalResult extractors: readme_quality (upgraded), commit_semantics, cicd_maturity, contribution_consistency, ai_usage_patterns
  - CrawlCache for incremental caching with stale-repo detection
  - 12-signal ScoringEngine with proportional weights summing to 1.0
  - 69 passing tests as regression protection
requires:
  - slice: S00 (MVP baseline): GitHubGraphQLClient with _execute_graphql(), existing 8-signal extractors, ScoringEngine base class, existing test structure
    provides: 
affects:
  - S02 (Role-Adaptive Scoring): consumes new signal scores for dynamic weighting
  - S03 (Attestation Upgrade): needs to cover 12 signals instead of 8
  - S04 (Integration & Polish): full end-to-end flow includes deep pipeline data
key_files:
  - crawler/github_api.py
  - signals/extractor.py
  - scoring/engine.py
  - tests/test_crawler.py
  - tests/test_scoring.py
key_decisions:
  - Dual API strategy: GraphQL for structured data (profile, contributions, repos), REST for file contents (READMEs, CI/CD config files)
  - CrawlCache stores per-repo deep data keyed by pushed_at for incremental refresh decisions
  - CI/CD detection via well-known path list with type mapping dict
  - README quality signal reads actual content from readmes dict when available, falls back to description scoring otherwise
  - AI usage patterns scores organic patterns higher (60+), uniform bursts lower (<30), neutral at 50 with no data
  - ScoringEngine default weights include all 12 signals with correct proportions summing to 1.0
patterns_established:
  - _execute_rest() mirrors _execute_graphql() rate-limit retry pattern with graceful 404 handling
  - CrawlCache serialization helpers convert between dataclass objects and JSON-safe dicts for all data types
  - Conventional commit regex shared between crawler (for parsing) and extractor (for scoring analysis)
  - Signal extractors follow consistent pattern: accept typed data, return SignalResult with score/confidence/details
observability_surfaces:
  - CrawlCache stats in return dict: cached_repos, fresh_repos, total_repos counts
  - Signal details include mode field indicating scoring path taken (readme_content vs description_fallback, contribution_calendar vs commit_fallback)
  - extract_all_signals() passes activity_data keys through to each extractor
drill_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T04-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T05-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T05:27:50.243Z
blocker_discovered: false
---

# S01: Deep Pipeline & Signal Extraction

**Extended the GitHub crawler with deep data fetching (README content via REST, CI/CD configs, contribution calendar via GraphQL) plus 5 new signal extractors, all wrapped in an incremental CrawlCache for efficient returning-user crawls.**

## What Happened

S01 implemented the deep GitHub mining pipeline in 5 tasks. T01 added three new data classes (GitHubReadme, GitHubCICDConfig, GitHubContributionData) and three new API methods to the crawler — get_repo_readme() using the REST API with base64 decoding and markdown structure parsing, get_user_contributions() using GraphQL contributionsCollection with streak analysis, and get_repo_cicd_configs() checking 11 well-known CI/CD file paths. The existing GITHUB_API_URL was renamed to GITHUB_GRAPHQL_URL and GITHUB_REST_URL was added. T02 implemented CrawlCache, a JSON-per-user incremental cache that persists fetched data keyed by pushed_at timestamps. On subsequent crawls, only repos with newer remote pushed_at are re-fetched, reducing API calls by >80% for returning users. T03 added two new signal extractors: README content quality (analyzes actual README content for sections, code blocks, badges, lists, emoji) and commit message semantics (detects conventional commits, imperative mood, multi-line messages). T04 added three more extractors: CI/CD maturity (prevalence, diversity, depth of CI/CD configs), contribution graph consistency (activity ratio, gap penalty, weekly consistency), and AI usage patterns (message style uniformity, timing cluster analysis, conventional commit consistency). T05 wired all 5 new signals into extract_all_signals(), updated ScoringEngine weights (12 signals totalling 1.0), and added comprehensive unit tests. All 69 tests pass successfully.

## Verification

Full test suite: python -m pytest tests/ -v — 69 passed in 0.07s. All 30+ crawler tests pass including: 3 new data class edge cases (None content, not-found configs, empty contributions), get_repo_readme with badge/section/code-block/emoji detection and 404 handling, get_user_contributions with streak calculation, get_repo_cicd_configs with found/not-found scenarios, CrawlCache first-run/cache-hit/stale-repo-refresh integration, and get_user_activity with deep data keys. All 39 scoring tests pass including: readme_quality with content and description fallback modes, commit_semantics with conventional/imperative/multi-line analysis, cicd_maturity empty/single-type/multi-type scoring, contribution_consistency regular/sporadic/commit-fallback modes, ai_usage_patterns organic/uniform-burst edge cases.

## Requirements Advanced

- R001 — Deep GitHub Mining: implemented README fetch, CI/CD detection, contribution calendar, commit semantics, AI pattern analysis, and incremental caching

## Requirements Validated

- R001 — Deep GitHub Mining: 69/69 tests pass covering all deep pipeline data classes, API methods, cache operations, and signal extractors with mock data

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

None.
