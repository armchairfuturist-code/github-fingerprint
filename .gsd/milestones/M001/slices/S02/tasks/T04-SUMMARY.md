---
id: T04
parent: S02
milestone: M001
key_files:
  - tests/test_scoring.py
key_decisions:
  - Scoring behavior tests use mock SignalResult objects for deterministic, repeatable verification of profile-specific scoring without network dependencies.
  - Backward compatibility test verifies that score_user() without role uses legacy weights (profile_name='legacy'), not engineering profile, ensuring pre-S02 callers are unaffected.
duration: 
verification_result: passed
completed_at: 2026-05-12T05:57:19.174Z
blocker_discovered: false
---

# T04: Added 6 comprehensive tests for role-adaptive scoring: profile-specific weights, confidence threshold filtering, role switching, backward compatibility, and profile-aware risk flags.

**Added 6 comprehensive tests for role-adaptive scoring: profile-specific weights, confidence threshold filtering, role switching, backward compatibility, and profile-aware risk flags.**

## What Happened

The verification gate found a pytest exit code 2 failure in the prior attempt, but after investigation the actual test state was healthy — all 123 tests passed. The real gap was coverage: the task plan specified 6 scoring behavior tests that didn't exist yet.

Added 6 new tests to test_scoring.py:

1. **test_scoring_engine_with_role_engineering** — Verifies that scoring with engineering profile produces different results than legacy default weights. Uses 12 mock SignalResult objects with deterministic scores, comparing engineering vs legacy engine output.

2. **test_scoring_engine_with_role_marketing** — Proves that engineering and marketing profiles produce distinct scores for identical input data by comparing engines initialized with each profile.

3. **test_scoring_engine_role_switching** — Validates that set_role() changes weights correctly (marketing → readme_quality=0.20, non-technical → project_ownership=0.20) and that all three profiles produce distinct scores from the same input data.

4. **test_confidence_threshold_filtering** — Verifies the core confidence filtering logic: signals below their profile threshold are excluded, weight is redistributed to remaining active signals, and _last_signals_below tracks the excluded names. Only readme_quality (confidence 0.5 ≥ threshold 0.3) remains active, producing a score of 55.0.

5. **test_score_user_backward_compatible** — Confirms that score_user() without role uses legacy weights (profile_name='legacy'), that calling with role=None is equivalent, and that calling with explicit role='engineering' switches to engineering profile.

6. **test_generate_risk_flags_with_confidence_thresholds** — Verifies that generate_risk_flags() produces profile-specific "Insufficient confidence in {signal} for {profile} profile" flags when signals_below_threshold is provided, in addition to standard low-score and low-confidence flags.

## Verification

python -m pytest tests/ -v --tb=short passed all 129 tests (6 new + 123 existing) in 0.23s. No regressions. No failures.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/ -v --tb=short` | 0 | ✅ pass | 230ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_scoring.py`
