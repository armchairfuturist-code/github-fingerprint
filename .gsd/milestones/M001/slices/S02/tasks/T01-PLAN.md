---
estimated_steps: 23
estimated_files: 2
skills_used: []
---

# T01: Define RoleProfile dataclass and built-in role profiles

Why: The scoring engine needs a structured way to represent role-specific signal weights and confidence thresholds. This task creates the foundational data model and at least 3 built-in profiles (engineering, marketing, non-technical) with distinct signal weight distributions.

Files: `scoring/profiles.py`, `scoring/__init__.py`

Do:
1. Create `scoring/profiles.py` with RoleProfile dataclass:
   - name: str (machine key, e.g. 'engineering')
   - display_name: str (human-readable)
   - description: str
   - weights: Dict[str, float] (signal_name -> weight, must sum to 1.0)
   - confidence_thresholds: Dict[str, float] (signal_name -> min confidence [0-1])
2. Add a helper function `get_profile(name: str) -> RoleProfile` that retrieves a profile by name, raises ValueError for unknown names.
3. Add a helper function `list_profiles() -> List[RoleProfile]` returning all built-in profiles.
4. Add a helper `resolve_role_profile(role: Optional[str]) -> RoleProfile` that returns engineering profile when role is None (backward compat).
5. Define 3 profiles with substantively different weights:
   - **Engineering** (default): commit_consistency=0.12, pr_patterns=0.12, commit_semantics=0.10, cicd_maturity=0.10, language_diversity=0.08, response_time=0.08, review_patterns=0.08, issue_engagement=0.08, readme_quality=0.06, project_ownership=0.06, contribution_consistency=0.06, ai_usage_patterns=0.06 (sum=1.0). Thresholds: tech signals >=0.4, soft >=0.3
   - **Marketing**: readme_quality=0.20, project_ownership=0.15, issue_engagement=0.15, review_patterns=0.10, commit_semantics=0.08, response_time=0.08, pr_patterns=0.06, language_diversity=0.06, commit_consistency=0.04, cicd_maturity=0.04, contribution_consistency=0.02, ai_usage_patterns=0.02 (sum=1.0). Thresholds: comms signals >=0.3, code signals >=0.2
   - **Non-technical**: project_ownership=0.20, issue_engagement=0.20, review_patterns=0.12, readme_quality=0.10, response_time=0.08, pr_patterns=0.08, language_diversity=0.06, commit_semantics=0.04, commit_consistency=0.04, cicd_maturity=0.03, contribution_consistency=0.03, ai_usage_patterns=0.02 (sum=1.0). Thresholds: project signals >=0.25, code signals >=0.1
6. Update `scoring/__init__.py` to export RoleProfile and helper functions.
7. Add validation that all profile weights sum to 1.0 (approximately, within float tolerance).

Constraints:
- All 12 signal names must be present in every profile's weights dict
- Every profile must have a confidence_thresholds dict covering all 12 signals
- Weights summed to 1.0 per profile (within 0.001 tolerance)
- Keep engineering profile weights close to existing defaults for backward compatibility

## Inputs

- `scoring/engine.py`

## Expected Output

- `scoring/profiles.py`
- `scoring/__init__.py`

## Verification

python -c "from scoring.profiles import list_profiles, get_profile; profiles = list_profiles(); assert len(profiles) >= 3; p = get_profile('engineering'); assert abs(sum(p.weights.values()) - 1.0) < 0.001; print('OK:', len(profiles), 'profiles')"
