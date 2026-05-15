---
id: S02
parent: M001
milestone: M001
provides:
  - Role-adaptive scoring engine with 3 built-in profiles and confidence threshold filtering
  - /profiles API endpoint for UI/API discovery of available profiles
  - Weight redistribution logic for below-threshold signals
  - Two-tier profile matching in /match endpoint
requires:
  - slice: S01
    provides: ScoringEngine from scoring/engine.py, SignalResult from signals/extractor.py
affects:
  - S03: Attestation Upgrade — needs to sign profile-aware scores
  - S04: Integration & Polish — needs to wire role parameter through frontend
key_files:
  - scoring/profiles.py
  - scoring/__init__.py
  - scoring/engine.py
  - api/main.py
  - tests/test_scoring.py
  - tests/test_api.py
key_decisions:
  - RoleProfile validation at construction time catches bad data early via __post_init__
  - resolve_role_profile(None) returns engineering for backward compatibility
  - ScoringEngine default constructor uses legacy weights (not engineering profile) for backward compat
  - Weight redistribution uses original_weight/sum_of_active_weights without mutating weights dict
  - /match uses two-tier strategy: profile matching first, keyword fallback second for unmatched descriptions
  - /profiles endpoint returns flat weights dict rather than full RoleProfile dataclass
  - Custom weights in /score override profile weights when both are specified
patterns_established:
  - RoleProfile validation enforced at construction time via __post_init__
  - ScoringEngine lazy initialization: legacy weights default, set_role()/role parameter for opt-in role-adaptive paths
  - Two-tier profile matching: structured profile match first, keyword-based fallback second
observability_surfaces:
  - ScoreResult.details includes profile_name and signals_below_threshold fields for debugging
  - Confidence threshold violations appear in risk_flags alongside existing low-confidence flags
drill_down_paths:
  - .gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T04-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-12T06:01:20.842Z
blocker_discovered: false
---

# S02: Role-Adaptive Scoring

**Scoring engine supports multiple role profiles (engineering, marketing, non-technical) with distinct signal weights and confidence thresholds. /profiles endpoint added for UI discovery. /match endpoint upgraded from keyword-map hacking to proper profile-based matching.**

## What Happened

S02 transformed the single flat-weight scoring engine into a role-adaptive system. We added three built-in role profiles with distinct weight distributions and per-signal confidence thresholds, confidence filtering with proportional weight redistribution, and a full profile-aware API surface.

T01 created the RoleProfile dataclass with __post_init__ validation (weights sum to 1.0, all 12 signals present, thresholds in [0,1]), 3 built-in profiles (engineering, marketing, non-technical), and helper functions list_profiles(), get_profile(), and resolve_role_profile().

T02 updated the ScoringEngine to support role-adaptive scoring: set_role() for stateful role switching, per-signal confidence threshold filtering, proportional weight redistribution when signals are excluded, and ScoreResult.details enriched with profile_name, signals_below_threshold, and signals_scored fields.

T03 wired role-adaptive scoring into all three FastAPI endpoints: /score gained a role parameter that resolves to profile weights before custom weight overrides; /match replaced keyword-map-only matching with a two-tier strategy (profile matching first, keyword fallback second); /profiles was added as a discovery endpoint exposing profile metadata.

T04 added comprehensive tests covering profile-specific weights, confidence threshold filtering, role switching, backward compatibility without roles (legacy weights preserved), and profile-aware risk flags.

## Verification

All 129 tests pass (97 from test_scoring.py + 32 from test_api.py) in 0.18s. Verification commands confirmed: 3+ profiles listed, engineering profile weights sum to 1.0, role switching produces correct weights/thresholds, confidence filtering excludes low-confidence signals, weight redistribution preserves relative importance, /profiles endpoint registered, /score endpoint accepts and rejects role parameters correctly, backward compatibility preserved for legacy callers.

## Requirements Advanced

- R002 — Role-adaptive scoring delivers 3 built-in profiles, confidence threshold filtering, weight redistribution, /profiles endpoint, and profile-aware /match endpoint.

## Requirements Validated

- R002 — 129/129 tests pass including 22 role-adaptive/profile-specific tests. 3 built-in profiles with distinct weights. /profiles endpoint serves profile metadata. /score?role=marketing returns different scores than default. Confidence threshold exclusion with proportional weight redistribution verified.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

GITHUB_TOKEN is required at import time in api/main.py — test collection requires the env var to be set even though API unit tests mock HTTP calls. A future improvement would defer the token check to endpoint invocation time for cleaner test isolation.

## Follow-ups

S03 (Attestation Upgrade): wire Ed25519 attestation signatures over scores and signals. S04 (Integration & Polish): end-to-end flow with incremental updates.

## Files Created/Modified

- `scoring/profiles.py` — New module: RoleProfile dataclass, 3 built-in profiles, list_profiles/get_profile/resolve_role_profile helpers
- `scoring/__init__.py` — Updated exports to include profiles module
- `scoring/engine.py` — Updated ScoringEngine with set_role(), confidence threshold filtering, weight redistribution, enriched ScoreResult.details
- `api/main.py` — Added role parameter to /score, two-tier profile matching to /match, new /profiles endpoint
- `tests/test_scoring.py` — Added 22 role-adaptive and profile-specific tests
- `tests/test_api.py` — Added 32 API tests covering /score with role, /match with profile matching, /profiles endpoint
