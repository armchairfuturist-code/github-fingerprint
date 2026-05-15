---
estimated_steps: 10
estimated_files: 3
skills_used: []
---

# T04: Port scoring engine and role profiles to Rust

Port the scoring engine from scoring/engine.py to Rust scoring-core:
- ScoringEngine struct with weights HashMap, confidence_thresholds, role_profile
- calculate_overall_score(): confidence filtering, proportional weight redistribution
- generate_risk_flags(): low scores, low confidence, threshold violations
- set_role(): load profile weights/thresholds
- score(): full pipeline: extract signals → calculate → risk flags → ScoreOutput

Port profiles from scoring/profiles.py:
- engineering, marketing, non-technical profiles with correct weights and thresholds
- list_profiles(), resolve_role_profile(name), get_profile(name) functions

Output: ScoringEngine compiles. ScoreOutput matches Python reference for same input.

## Inputs

- `scoring/engine.py`
- `scoring/profiles.py`

## Expected Output

- `scoring-core/src/engine.rs`
- `scoring-core/src/profiles.rs`

## Verification

cargo test. Run 5 test profiles through Rust engine, compare against Python engine output. Scores match within ±0.5. Risk flags match.
