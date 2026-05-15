---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T04: Add CI/CD maturity, contribution graph consistency, and AI usage pattern signals

Implement three new signal extractors: (1) CI/CD maturity — score based on number and variety of CI/CD configs detected (GitHub Actions = 20pts, other CI systems = 15pts each, Dockerfile = 10pts). Higher for multiple CI types across repos; (2) Contribution graph consistency — analyze commit density patterns using contribution calendar data. Score based on regular vs bursty patterns. Detect long gaps (30+ days). Higher for consistent spread; (3) AI usage patterns — analyze commit timing clusters (are commits evenly distributed or clumped in short windows?), message style uniformity (standard deviation of message length, conventional commit consistency). Score based on natural-looking patterns (moderate variance = organic, very low variance + bursts = potentially AI-assisted). All return 0-100 scores with confidence metrics.

## Inputs

- `signals/extractor.py`
- `crawler/github_api.py`

## Expected Output

- `signals/extractor.py`

## Verification

python -m pytest tests/test_scoring.py -x -v
