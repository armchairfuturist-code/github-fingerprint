---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Add README content quality and commit message semantics signals

Implement two new signal extractors: (1) README content quality — upgrade from repo-description-only to analyzing actual README content (character count, section headers, code blocks, list count, badge detection, emoji presence). Score based on README completeness vs empty/missing; (2) Commit message semantics — analyze commit messages for conventional commit patterns (feat:, fix:, docs:, etc.), average message length, multi-line message ratio, imperative mood usage. Score higher for structured, descriptive messages. Both signals return 0-100 scores with confidence metrics.

## Inputs

- `signals/extractor.py`
- `crawler/github_api.py`

## Expected Output

- `signals/extractor.py`

## Verification

python -m pytest tests/test_scoring.py -x -v
