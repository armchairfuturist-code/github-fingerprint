---
id: T02
parent: S02
milestone: M001
key_files:
  - scoring/engine.py
  - tests/test_scoring.py
key_decisions:
  - ScoringEngine default constructor uses legacy weights (not engineering profile) to guarantee backward compatibility with pre-S02 callers
  - Weight redistribution uses original_weight / sum_of_active_weights — the weights dict is never mutated, redistribution is computed at scoring time
  - confidence_thresholds empty in legacy mode means all signals pass through, preserving original behavior
  - set_role() mutates engine state; score_user() with role parameter provides a convenience path for one-shot role switching
duration: 
verification_result: passed
completed_at: 2026-05-12T05:50:24.761Z
blocker_discovered: false
---

# T02: Updated ScoringEngine for role-adaptive scoring with confidence threshold filtering, weight redistribution, and profile-aware risk flags

**Updated ScoringEngine for role-adaptive scoring with confidence threshold filtering, weight redistribution, and profile-aware risk flags**

## What Happened

Updated scoring/engine.py with full role-adaptive scoring support:
- ScoringEngine.__init__ now accepts an optional `profile` parameter (string or RoleProfile) alongside the existing `weights` parameter. When neither is provided, legacy default weights are used for full backward compatibility.
- Added `set_role(profile_name)` method that loads a named profile's weights and confidence thresholds via `resolve_role_profile()` from the profiles module.
- Added `confidence_thresholds` instance variable (Dict[str, float]), populated from the active profile or empty in legacy mode.
- Modified `calculate_overall_score()` to filter signals whose confidence is below their per-signal threshold. Filtered signals' weight is redistributed proportionally among remaining active signals (original_weight / sum_of_active_weights). When no thresholds are set (legacy mode), all signals pass through unchanged.
- Modified `generate_risk_flags()` to accept an optional `signals_below_threshold` parameter and add profile-specific flags: "Insufficient confidence in {signal_name} for {profile} profile".
- Modified `score_user()` to accept an optional `role: Optional[str] = None` parameter that calls `set_role()` before scoring when provided.
- Updated ScoreResult.details with `profile_name`, `signals_below_threshold` (list), and `signals_scored` (int) fields.
- Added 6 negative tests covering: unknown profile in set_role, invalid constructor profile, empty signals, all signals below threshold, unrecognized signal names, and profile details verification.
- All 39 existing tests pass unchanged, confirming backward compatibility.

## Verification

Full test suite: 45/45 passed (39 existing + 6 new negative tests). Task plan verification command: python -c role switching works. Manual verification confirmed: profile switching produces correct weights/thresholds, confidence filtering excludes low-confidence signals, weight redistribution preserves relative importance, risk flags include both old (confidence<0.3) and new (profile threshold) violation flags, ScoreResult.details includes profile_name/signals_below_threshold/signals_scored.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_scoring.py -v --tb=short` | 0 | ✅ pass | 70ms |
| 2 | `python -c 'from scoring.engine import ScoringEngine; e = ScoringEngine(); assert len(e.weights) == 12; e.set_role("marketing"); assert e.weights["readme_quality"] == 0.20; print("OK: role switching works")'` | 0 | ✅ pass | 580ms |
| 3 | `python -c comprehensive verification of confidence filtering, weight redistribution, risk flags, and backward compat` | 0 | ✅ pass | 650ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scoring/engine.py`
- `tests/test_scoring.py`
