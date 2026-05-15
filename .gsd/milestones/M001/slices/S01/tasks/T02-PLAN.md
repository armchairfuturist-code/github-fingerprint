---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Add incremental crawl cache for returning users

Implement a CrawlCache class that persists fetched GitHub data per username using JSON files stored in a .crawl_cache/ directory. The cache stores: (a) a snapshot of the latest crawl timestamp; (b) fetched data keyed by repo name with pushed_at timestamps. On subsequent crawls, only re-fetch repos where the remote pushed_at is newer than the cached pushed_at. Merge cached data with new data. Return delta stats (cached_repos, fresh_repos). Handle empty cache gracefully. Include cache_stats in the return dict so callers know hit/miss counts.

## Inputs

- `crawler/github_api.py`

## Expected Output

- `crawler/github_api.py`

## Verification

python -m pytest tests/test_crawler.py -x -v
