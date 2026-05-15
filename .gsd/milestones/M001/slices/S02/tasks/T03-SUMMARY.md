---
id: T03
parent: S02
milestone: M001
key_files:
  - api/main.py
  - tests/test_api.py
key_decisions:
  - Role resolution in /score uses validate-first pattern: resolve_role_profile validates before set_role applies
  - Profile matching in /match uses two-tier strategy: profile matching first, keyword fallback second
  - /profiles endpoint returns flat weights dict rather than full RoleProfile dataclass
  - Custom weights in /score override profile weights when both are specified
  - /match is lenient by design — unmatched descriptions produce keyword-boosted results instead of errors
duration: 
verification_result: passed
completed_at: 2026-05-12T05:55:17.267Z
blocker_discovered: false
---

# T03: Wired role-adaptive scoring into all three FastAPI endpoints: /score gains role parameter with profile switching, /match replaces keyword-map with profile-based matching, /profiles endpoint added for UI discovery.

**Wired role-adaptive scoring into all three FastAPI endpoints: /score gains role parameter with profile switching, /match replaces keyword-map with profile-based matching, /profiles endpoint added for UI discovery.**

## What Happened

Updated api/main.py with all planned changes:

1. **ScoreRequest model**: Added optional `role: Optional[str] = None` field
2. **ScoreResponse model**: Added `profile: str` field populated from `score_result.details.profile_name`
3. **/score POST**: Now accepts `request.role`, validates it via `resolve_role_profile()`, then applies `set_role()` before scoring. Custom weights override profile weights when both are provided. Unknown role names return HTTP 400 via the existing ValueError handler.
4. **/score/{username} GET**: Added `role: Optional[str] = Query(None)` parameter, passed through to POST handler via ScoreRequest.
5. **Replaced _extract_role_keywords()**: The function is preserved as a keyword-boost fallback, but a new `_resolve_role_for_matching()` function now tries profile name/display_name substring matching and term-based classification (engineering, marketing, non-technical keyword sets) before falling back to keyword boosts.
6. **/match POST**: Updated to use `_resolve_role_for_matching()` — when a known profile matches, the user is scored with that profile's weights and given profile-aware reasons. When unmatched, falls back to legacy keyword-boost behavior for backward compatibility.
7. **/profiles GET**: New endpoint returning `ProfilesListResponse` wrapping `ProfileResponse` objects (name, display_name, description, weights as flat dict — not the full RoleProfile dataclass).
8. **Error handling**: Invalid role names in /score return 400. /match is lenient — unmatched descriptions fall back gracefully.
9. **ProfileResponse model**: New Pydantic model for serializing profiles without exposing internal dataclass structure.

## Verification

All 123 tests pass (32 new API tests + 91 existing tests). The `/profiles` endpoint is registered in FastAPI routes. The `/score` endpoint correctly accepts and rejects role parameters. The `_resolve_role_for_matching` function handles exact matches, partial matches, case-insensitive matches, term-based classification, and keyword fallback.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_api.py -v` | 0 | pass | 210ms |
| 2 | `pytest -v` | 0 | pass | 180ms |
| 3 | `python -c 'from api.main import app; assert "/profiles" in [r.path for r in app.routes]'` | 0 | pass | 150ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `api/main.py`
- `tests/test_api.py`
