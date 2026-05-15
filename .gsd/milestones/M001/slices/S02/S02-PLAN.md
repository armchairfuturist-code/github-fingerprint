# S02: Role-Adaptive Scoring

**Goal:** Move from a single flat-weight scoring engine to a role-adaptive system with multiple role profiles (engineering, marketing, non-technical), per-signal confidence thresholds, and a profiles API. The `/score` endpoint gains a `role` parameter; the `/match` endpoint switches from keyword hacking to proper profile-based matching.
**Demo:** Scoring engine supports multiple role profiles with different signal weights.

## Must-Haves

- `python -m pytest tests/ -v -k "role_adaptive or profile"` passes with 15+ tests. `python -m pytest tests/ -v` passes all existing tests (backward compat). API serves `/profiles` listing >= 3 profiles. `/score?role=marketing` returns different scores than `/score` for same user data. Signals below confidence threshold are excluded from weighted score with proportional redistribution.

## Proof Level

- This slice proves: contract

## Integration Closure

Consumes ScoringEngine from `scoring/engine.py` and SignalResult from `signals/extractor.py`. New `scoring/profiles.py` module introduced. API layer in `api/main.py` updated to pass role parameter through to scoring engine. Remaining before milestone end-to-end: S03 (attestation upgrade) and S04 (integration & polish).

## Verification

- ScoreResult.details gains `profile_name` and `signals_below_threshold` fields. /profiles endpoint exposes available profiles for UI discovery. Confidence threshold violations appear in risk_flags.

## Tasks

- [x] **T01: Define RoleProfile dataclass and built-in role profiles** `est:30m`
  Why: The scoring engine needs a structured way to represent role-specific signal weights and confidence thresholds. This task creates the foundational data model and at least 3 built-in profiles (engineering, marketing, non-technical) with distinct signal weight distributions.
  - Files: `scoring/profiles.py`, `scoring/__init__.py`
  - Verify: python -c "from scoring.profiles import list_profiles, get_profile; profiles = list_profiles(); assert len(profiles) >= 3; p = get_profile('engineering'); assert abs(sum(p.weights.values()) - 1.0) < 0.001; print('OK:', len(profiles), 'profiles')"

- [x] **T02: Update ScoringEngine for role-adaptive scoring with confidence filtering** `est:45m`
  Why: The ScoringEngine currently uses a single flat weight set with no role awareness and no confidence thresholding. This task makes it role-adaptive: it can load profile-specific weights and apply per-signal confidence filters, redistributing weight from below-threshold signals proportionally.
  - Files: `scoring/engine.py`
  - Verify: python -c "from scoring.engine import ScoringEngine; e = ScoringEngine(); assert len(e.weights) == 12; e.set_role('marketing'); assert e.weights['readme_quality'] == 0.20; print('OK: role switching works')"

- [x] **T03: Wire role-adaptive scoring into the FastAPI endpoints** `est:30m`
  Why: The API currently accepts custom weights but has no concept of role profiles. The /match endpoint uses a primitive keyword-map approach (_extract_role_keywords) that doesn't leverage the new profiles. This task updates both endpoints and adds a /profiles discovery endpoint.
  - Files: `api/main.py`
  - Verify: python -c "from api.main import app; routes = [r.path for r in app.routes]; assert '/profiles' in routes; print('OK: /profiles endpoint registered')"

- [x] **T04: Comprehensive tests for role-adaptive scoring** `est:45m`
  Why: The role-adaptive scoring system introduces multiple code paths (3 profiles, confidence filtering, weight redistribution, API contracts). Each path needs test coverage to prevent regressions. This task adds 15+ tests covering profile definitions, scoring behavior, confidence thresholds, API contracts, and backward compatibility.
  - Files: `tests/test_scoring.py`, `tests/test_api.py`
  - Verify: python -m pytest tests/ -v --tb=short 2>&1 | tail -5

## Files Likely Touched

- scoring/profiles.py
- scoring/__init__.py
- scoring/engine.py
- api/main.py
- tests/test_scoring.py
- tests/test_api.py
