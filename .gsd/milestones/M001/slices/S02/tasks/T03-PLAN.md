---
estimated_steps: 19
estimated_files: 1
skills_used: []
---

# T03: Wire role-adaptive scoring into the FastAPI endpoints

Why: The API currently accepts custom weights but has no concept of role profiles. The /match endpoint uses a primitive keyword-map approach (_extract_role_keywords) that doesn't leverage the new profiles. This task updates both endpoints and adds a /profiles discovery endpoint.

Files: `api/main.py`

Do:
1. Update `ScoreRequest` pydantic model to add optional `role: Optional[str] = None` field.
2. Update `ScoreResponse` to add `profile: str` field (name of profile used).
3. Update `/score` POST endpoint to pass `request.role` to `scoring_engine.score_user()`.
4. Update `/score/{username}` GET endpoint to accept `role: Optional[str] = Query(None)`.
5. Replace the `_extract_role_keywords()` function with proper profile-based matching:
   - Import profile helpers from scoring.profiles
   - When a role_description is provided, match it against profile display_names and descriptions using simple substring matching
   - Fall back to engineering profile with keyword boosts as before
6. Update `/match` endpoint to use resolved profile for scoring and generate better role-adapted reasons.
7. Add `/profiles` GET endpoint returning list of available profiles with name, display_name, description, and weights.
8. Add proper error handling for unknown role names (400 Bad Request).
9. Create a pydantic model `ProfileResponse` for the /profiles endpoint.

Constraints:
- Existing /score and /match endpoints without role parameter must produce identical results to pre-S02
- The /match endpoint should still work without a role_description (default to engineering profile)
- /profiles weights should be serialized as a flat dict, not the full RoleProfile dataclass

## Inputs

- `api/main.py`
- `scoring/profiles.py`
- `scoring/engine.py`

## Expected Output

- `api/main.py`

## Verification

python -c "from api.main import app; routes = [r.path for r in app.routes]; assert '/profiles' in routes; print('OK: /profiles endpoint registered')"
