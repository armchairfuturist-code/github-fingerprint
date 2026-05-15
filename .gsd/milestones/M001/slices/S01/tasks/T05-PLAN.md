---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T05: Integrate new signals into extractor, update API, and add comprehensive tests

Wire everything together: (1) Update SignalExtractor.extract_all_signals() to extract all 5 new signals alongside the existing 8; (2) Update ScoringEngine default weights to include all new signals — keep existing 8 weights proportional and add new signal weights that sum to 1.0; (3) Add unit tests in test_scoring.py for all new signals with mock data (README text, messages, contribution data, CI/CD configs); (4) Add crawler tests in test_crawler.py for new methods (get_repo_readme, get_user_contributions, get_repo_cicd_configs) with proper mocks; (5) Add a crawl cache test verifying hit/miss behavior; (6) Run full test suite and fix any regressions.

## Inputs

- `signals/extractor.py`
- `scoring/engine.py`
- `tests/test_crawler.py`
- `tests/test_scoring.py`
- `crawler/github_api.py`

## Expected Output

- `signals/extractor.py`
- `scoring/engine.py`
- `tests/test_crawler.py`
- `tests/test_scoring.py`

## Verification

python -m pytest tests/ -x -v
