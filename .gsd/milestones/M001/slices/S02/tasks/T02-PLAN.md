---
estimated_steps: 25
estimated_files: 1
skills_used: []
---

# T02: Update ScoringEngine for role-adaptive scoring with confidence filtering

Why: The ScoringEngine currently uses a single flat weight set with no role awareness and no confidence thresholding. This task makes it role-adaptive: it can load profile-specific weights and apply per-signal confidence filters, redistributing weight from below-threshold signals proportionally.

Files: `scoring/engine.py`

Do:
1. Import RoleProfile helpers from scoring.profiles.
2. Change `__init__` to accept optional `profile` (string name or RoleProfile instance). If None, defaults to engineering profile.
3. Add `set_role(profile_name: str)` method that loads the named profile and updates self.weights and self.confidence_thresholds.
4. Add `confidence_thresholds` instance variable (Dict[str, float]). Default from loaded profile.
5. Modify `calculate_overall_score()` to:
   - Before calculating, filter signals whose confidence is below their threshold
   - Move filtered signals' weight proportionally to remaining active signals
   - Store filtered signal names for the details dict
   - Original behavior preserved when no thresholds are set
6. Modify `generate_risk_flags()` to:
   - Add flags for signals below confidence threshold: "Insufficient confidence in {signal name} for {profile} profile"
7. Modify `score_user()` to accept optional `role: Optional[str] = None` parameter. When provided, call `set_role(role)` before scoring.
8. Update `ScoreResult.details` to include:
   - `profile_name`: the profile used
   - `signals_below_threshold`: list of signal names that fell below confidence
   - `signals_scored`: count of signals that contributed
9. Ensure backward compatibility: no role = engineering profile (same weights as before for engineering).

Important design note on weight redistribution: When a signal is excluded due to low confidence, its weight is redistributed proportionally among the remaining signals. E.g., if signal A (weight 0.12) is excluded and the remaining 11 signals sum to 0.88, each remaining signal's effective weight = original_weight / 0.88. This preserves the profile's relative importance structure.

Constraints:
- All existing tests must pass unchanged
- score_user() without role must produce same scores as pre-S02 for same data
- The `weights` dict is always the full profile weights; the redistribution is computed at scoring time

## Inputs

- `scoring/profiles.py`
- `scoring/engine.py`

## Expected Output

- `scoring/engine.py`

## Verification

python -c "from scoring.engine import ScoringEngine; e = ScoringEngine(); assert len(e.weights) == 12; e.set_role('marketing'); assert e.weights['readme_quality'] == 0.20; print('OK: role switching works')"
