# S01: Deep GitHub Pipeline

**Goal:** Extend the GitHub crawler pipeline with deep data fetching (README content, CI/CD configs, contribution calendar, commit message semantics) plus 5 new signal extractors, all wrapped in an incremental cache so returning users get <20% of original API calls.
**Demo:** Crawler fetches README content, detects CI/CD configs, analyzes commit patterns, and caches results for incremental updates.

## Must-Haves

- Crawler fetches actual README content (not just repo description) for each repo via REST API\n- Crawler detects CI/CD configuration files (.github/workflows, Jenkinsfile, .circleci/config.yml, etc.)\n- Crawler analyzes contribution graph (commit density over time via contributionsCollection)\n- Crawler extracts commit message patterns (conventional commits, length, structure)\n- Crawler detects AI usage patterns (timing clusters, message style uniformity)\n- Incremental cache: second crawl of same user fetches <20% of original API calls\n- All new data classes, queries, and signal extractors have unit test coverage\n- Existing tests continue to pass

## Proof Level

- This slice proves: contract — all new extractors have unit tests with mock data proving score stability

## Integration Closure

Upstream: GitHub GraphQL API (README, contributionsCollection), REST API (CI/CD file checks). New wiring: deep pipeline data flows into existing get_user_activity() return dict with new keys. Downstream: S02 consumes new signal scores for role-adaptive weighting.

## Verification

- Runtime signals: structured log at each crawl phase (user data → repos → deep per-repo data → contributions → signals). Crawl cache hit/miss logged per user. Failure visibility: partial crawl data includes which phases completed; missing fields are null with logged reason.

## Tasks

- [x] **T01: Add deep pipeline data classes and GraphQL/REST queries** `est:1h`
  Add new data types and API methods to the crawler for the deep pipeline. This includes: (1) data classes for README content, CI/CD configs, contribution calendar data; (2) a get_repo_readme() method using REST API; (3) a get_user_contributions() method using GraphQL contributionsCollection; (4) a get_repo_cicd_configs() method checking well-known CI/CD file paths; (5) update get_user_activity() to include deep data under new keys. The REST API calls should use the existing requests session with the same auth headers.
  - Files: `crawler/github_api.py`
  - Verify: python -m pytest tests/test_crawler.py -x -v

- [x] **T02: Add incremental crawl cache for returning users** `est:45m`
  Implement a CrawlCache class that persists fetched GitHub data per username using JSON files stored in a .crawl_cache/ directory. The cache stores: (a) a snapshot of the latest crawl timestamp; (b) fetched data keyed by repo name with pushed_at timestamps. On subsequent crawls, only re-fetch repos where the remote pushed_at is newer than the cached pushed_at. Merge cached data with new data. Return delta stats (cached_repos, fresh_repos). Handle empty cache gracefully. Include cache_stats in the return dict so callers know hit/miss counts.
  - Files: `crawler/github_api.py`
  - Verify: python -m pytest tests/test_crawler.py -x -v

- [x] **T03: Add README content quality and commit message semantics signals** `est:1h`
  Implement two new signal extractors: (1) README content quality — upgrade from repo-description-only to analyzing actual README content (character count, section headers, code blocks, list count, badge detection, emoji presence). Score based on README completeness vs empty/missing; (2) Commit message semantics — analyze commit messages for conventional commit patterns (feat:, fix:, docs:, etc.), average message length, multi-line message ratio, imperative mood usage. Score higher for structured, descriptive messages. Both signals return 0-100 scores with confidence metrics.
  - Files: `signals/extractor.py`
  - Verify: python -m pytest tests/test_scoring.py -x -v

- [x] **T04: Add CI/CD maturity, contribution graph consistency, and AI usage pattern signals** `est:1h`
  Implement three new signal extractors: (1) CI/CD maturity — score based on number and variety of CI/CD configs detected (GitHub Actions = 20pts, other CI systems = 15pts each, Dockerfile = 10pts). Higher for multiple CI types across repos; (2) Contribution graph consistency — analyze commit density patterns using contribution calendar data. Score based on regular vs bursty patterns. Detect long gaps (30+ days). Higher for consistent spread; (3) AI usage patterns — analyze commit timing clusters (are commits evenly distributed or clumped in short windows?), message style uniformity (standard deviation of message length, conventional commit consistency). Score based on natural-looking patterns (moderate variance = organic, very low variance + bursts = potentially AI-assisted). All return 0-100 scores with confidence metrics.
  - Files: `signals/extractor.py`
  - Verify: python -m pytest tests/test_scoring.py -x -v

- [x] **T05: Integrate new signals into extractor, update API, and add comprehensive tests** `est:1h`
  Wire everything together: (1) Update SignalExtractor.extract_all_signals() to extract all 5 new signals alongside the existing 8; (2) Update ScoringEngine default weights to include all new signals — keep existing 8 weights proportional and add new signal weights that sum to 1.0; (3) Add unit tests in test_scoring.py for all new signals with mock data (README text, messages, contribution data, CI/CD configs); (4) Add crawler tests in test_crawler.py for new methods (get_repo_readme, get_user_contributions, get_repo_cicd_configs) with proper mocks; (5) Add a crawl cache test verifying hit/miss behavior; (6) Run full test suite and fix any regressions.
  - Files: `signals/extractor.py`, `scoring/engine.py`, `tests/test_crawler.py`, `tests/test_scoring.py`
  - Verify: python -m pytest tests/ -x -v

## Files Likely Touched

- crawler/github_api.py
- signals/extractor.py
- scoring/engine.py
- tests/test_crawler.py
- tests/test_scoring.py
