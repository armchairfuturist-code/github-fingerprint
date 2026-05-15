# S01: Deep Pipeline & Signal Extraction — UAT

**Milestone:** M001
**Written:** 2026-05-12T05:27:50.243Z

## UAT: Deep GitHub Pipeline

### UAT Type
Integration verification — validates end-to-end data flow from GitHub API mocks through signal extraction.

### Preconditions
- Project root has `crawler/github_api.py`, `signals/extractor.py`, `scoring/engine.py`
- `tests/` directory contains `test_crawler.py` and `test_scoring.py`
- Python 3.14+ with pytest, requests, and required dependencies installed

### Test Steps

**Step 1: Verify deep API methods**
1. Run `python -m pytest tests/test_crawler.py::TestGitHubClient::test_get_repo_readme_success -v`
   → **Expected:** Test passes, README content is decoded from base64 with section/badge/code-block metadata
2. Run `python -m pytest tests/test_crawler.py::TestGitHubClient::test_get_user_contributions_success -v`
   → **Expected:** Test passes, returns GitHubContributionData with contribution days and streak info
3. Run `python -m pytest tests/test_crawler.py::TestGitHubClient::test_get_repo_cicd_configs_found -v`
   → **Expected:** Test passes, detects GitHub Actions config and Dockerfile

**Step 2: Verify incremental cache**
1. Run `python -m pytest tests/test_crawler.py::TestCrawlCache -v`
   → **Expected:** All 16 cache tests pass covering: save/load roundtrip, stale detection (no cache/all cached/mixed/newer remote), merge behavior (no cache/stale+fresh), and full integration test_cache_first_run, cache_hit_skips_fetching, cache_refreshes_stale_repo

**Step 3: Verify signal extraction**
1. Run `python -m pytest tests/test_scoring.py::test_extract_readme_quality_with_content -v`
   → **Expected:** Passes, readme_quality uses readme_content mode when readmes are available
2. Run `python -m pytest tests/test_scoring.py::test_cicd_maturity_multiple_types_higher -v`
   → **Expected:** Passes, multi-type CI/CD scores higher than single-type
3. Run `python -m pytest tests/test_scoring.py::test_contribution_consistency_regular -v`
   → **Expected:** Passes, regular daily pattern scores >50
4. Run `python -m pytest tests/test_scoring.py::test_ai_usage_patterns_suspicious -v`
   → **Expected:** Passes, uniform burst pattern scores <50

**Step 4: Full test suite**
1. Run `python -m pytest tests/ -v`
   → **Expected:** All 69 tests pass (39 scoring + 30 crawler), 0 failures

### Edge Cases Verified
- Empty data: all extractors return 0 score / neutral 50 / zero confidence when no data
- Null/None inputs: readme_quality falls back to description mode, contribution_consistency to commit-fallback
- 404 handling: get_repo_readme returns None (404), get_repo_cicd_configs returns empty list
- Cache edge cases: no cache dir, first run (all fresh), full cache hit, stale repo refresh
- AI pattern extremes: organic (moderate variance ≥50), suspicious uniform bursts (<50)
- CI/CD scoring single-type vs multi-type comparison

### Not Proven By This UAT
- Actual GitHub API integration (uses mocks — live API tested during e2e integration)
- Role-adaptive weighting (S02 scope)
- Ed25519 attestation of new signals (S03 scope)
- Per-user .crawl_cache/ directory creation outside tmp_path

