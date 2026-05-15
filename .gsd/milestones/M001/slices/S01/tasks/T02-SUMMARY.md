---
id: T02
parent: S01
milestone: M001
key_files:
  - crawler/github_api.py
  - tests/test_crawler.py
key_decisions:
  - CrawlCache stores per-repo deep data keyed by pushed_at for incremental refresh decisions
  - repos_data parallel dict avoids tagging individual commit/issue/PR objects with repo identity
  - get_user_activity() extends with use_cache param — backward compatible default use_cache=False
duration: 
verification_result: passed
completed_at: 2026-05-12T05:17:23.346Z
blocker_discovered: false
---

# T02: Added CrawlCache class with JSON-per-user incremental caching, stale-repo detection via pushed_at comparison, cache-aware get_user_activity(), and 16 new tests covering all cache operations

**Added CrawlCache class with JSON-per-user incremental caching, stale-repo detection via pushed_at comparison, cache-aware get_user_activity(), and 16 new tests covering all cache operations**

## What Happened

Implemented the CrawlCache class that persists fetched GitHub data per username using JSON files in a configurable .crawl_cache/ directory. The cache stores: (a) a last-crawled timestamp; (b) per-repo data keyed by full_name with pushed_at timestamps; (c) serialized commits, issues, PRs, README content, CI/CD configs, and contribution data.

Added serialization helpers for all data classes (GitHubCommit, GitHubIssue, GitHubPR, GitHubReadme, GitHubCICDConfig, GitHubContributionDay, GitHubContributionData) to convert between dataclass objects and JSON-safe dicts.

Key methods on CrawlCache:
- load/save/has — standard cache I/O
- get_stale_repos() — compares remote pushed_at against cached values; returns set of stale repo names + cache_stats dict (cached_repos, fresh_repos, total_repos)
- merge_deep_data() — merges fresh deep data for stale repos with cached deep data for unchanged repos; returns merged commits, issues, prs, readmes, cicd_configs, and repos_data
- build_entry() — converts a crawl result dict into a JSON-serializable cache entry

Modified get_user_activity() to accept use_cache and cache parameters. When caching is enabled, it only fetches deep data (commits, issues, PRs, README, CI/CD) for repos whose remote pushed_at is newer than cached. Unchanged repo data is merged from cache. The result includes a cache_stats key with hit/miss counts.

Added 16 new tests covering: cache init/dir creation, save/load roundtrip, new_entry structure, build_entry with deep data and contributions, stale repo detection (no cache, all cached, mixed, newer remote), merge behavior (no cache, stale+fresh repos), and full integration tests (first run fetches all, cache hit skips fetches, cache refresh for stale repos).

## Verification

All 46 tests pass: 30 existing + 16 new CrawlCache tests covering cache I/O, stale detection, merge logic, and get_user_activity integration with use_cache=True.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_crawler.py -x -v` | 0 | ✅ pass | 60ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `crawler/github_api.py`
- `tests/test_crawler.py`
