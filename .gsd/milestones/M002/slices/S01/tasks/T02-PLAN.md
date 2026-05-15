---
estimated_steps: 8
estimated_files: 2
skills_used: []
---

# T02: Define Rust data types (ScoreInput/ScoreOutput/Profile)

Define the data types in scoring-core:
- ScoreInput: mirrors the activity_data dict shape from Python (repos, commits, issues, prs)
- SignalScore: struct with score, confidence, details (HashMap<String, serde_json::Value>)
- ScoreOutput: struct with overall_score, signal_scores, risk_flags, profile_name, signals_below_threshold
- SignalConfig: name, weight, confidence_threshold
- RoleProfile: struct with name, display_name, description, weights, confidence_thresholds

All types derive Serialize + Deserialize. String enums where appropriate.

Output: All type definitions compile. Unit tests for construction and serialization.

## Inputs

- `scoring/engine.py (ScoreResult)`
- `scoring/profiles.py (RoleProfile)`
- `signals/extractor.py (SignalResult)`

## Expected Output

- `scoring-core/src/types.rs`

## Verification

cargo build. Unit test: create each struct, serialize to JSON, deserialize back, verify fields match.
