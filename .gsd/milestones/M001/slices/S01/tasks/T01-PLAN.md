---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Add deep pipeline data classes and GraphQL/REST queries

Add new data types and API methods to the crawler for the deep pipeline. This includes: (1) data classes for README content, CI/CD configs, contribution calendar data; (2) a get_repo_readme() method using REST API; (3) a get_user_contributions() method using GraphQL contributionsCollection; (4) a get_repo_cicd_configs() method checking well-known CI/CD file paths; (5) update get_user_activity() to include deep data under new keys. The REST API calls should use the existing requests session with the same auth headers.

## Inputs

- `crawler/github_api.py`

## Expected Output

- `crawler/github_api.py`

## Verification

python -m pytest tests/test_crawler.py -x -v
