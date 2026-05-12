# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

## Validated

### R001 — Untitled
- Status: validated
- Validation: S01 delivers deep pipeline: README content via REST API (get_repo_readme), CI/CD config detection (get_repo_cicd_configs covering 11 well-known path patterns), contribution calendar via GraphQL (get_user_contributions), commit message semantics analysis, and AI usage pattern detection. All 12 signals (8 original + 4 new) extracted and scored. Incremental freshness via CrawlCache with pushed_at comparison. 69/69 tests pass.

### R002 — The scoring engine supports multiple role profiles (engineering, marketing, non-technical) with distinct signal weight distributions and per-signal confidence thresholds. Users can specify a role when requesting a score, and signals below their confidence threshold are excluded with proportional weight redistribution. The /profiles endpoint exposes available profiles for UI or API discovery.
- Class: core-capability
- Status: validated
- Description: The scoring engine supports multiple role profiles (engineering, marketing, non-technical) with distinct signal weight distributions and per-signal confidence thresholds. Users can specify a role when requesting a score, and signals below their confidence threshold are excluded with proportional weight redistribution. The /profiles endpoint exposes available profiles for UI or API discovery.
- Why it matters: A single flat-weight scoring engine cannot distinguish between candidates for different roles. A marketing role values communication signals more than commit consistency, while engineering values code-related signals. Without role-adaptivity, the score is wrong for both.
- Source: Milestone M001 plan, D004 (scoring algorithm iteration model), milestone context
- Validation: S02 delivers role-adaptive scoring: 3 built-in profiles (engineering, marketing, non-technical) with distinct signal weights and per-signal confidence thresholds. ScoreResult.details includes profile_name and signals_below_threshold. /profiles endpoint exposes available profiles. /score?role=marketing returns different scores than default. Signals below confidence threshold excluded with proportional weight redistribution. 129/129 tests pass including 22 role-adaptive/profile-specific tests and 36 API tests covering all three endpoints.

### R003 — Score attestation — Every complete score response includes an independently verifiable Ed25519 signature covering the overall score and all signal scores. A /verify endpoint allows third parties to verify authenticity. Attestation gracefully degrades when no signing key is available (omits attestation block rather than crashing).
- Class: core-capability
- Status: validated
- Description: Score attestation — Every complete score response includes an independently verifiable Ed25519 signature covering the overall score and all signal scores. A /verify endpoint allows third parties to verify authenticity. Attestation gracefully degrades when no signing key is available (omits attestation block rather than crashing).
- Why it matters: Without attestation, scores are opaque server assertions that cannot be independently verified. The attestation signature enables third parties (recruiters, platforms) to verify that a score was genuinely produced by the fingerprint service and has not been tampered with. This is the foundation for the trust model described in D003: Ed25519 attestation is the instant safety net before async ZK proving is implemented.
- Source: Milestone M001 plan, D003 (async proving architecture with Ed25519 fallback), D008 (Ed25519 attestation approach)
- Validation: S03 delivers full Ed25519 attestation pipeline: sign_score, verify_attestation, and load_or_generate_signing_key in attest/ module; attestation blocks (signature, public_key, signed_payload, signed_at) in /score and /match responses via _build_attestation helper; POST /verify endpoint for third-party verification returning {valid, payload, error}; graceful degradation: omitted attestation block + warning log when key is unavailable. 161 tests pass including 18 attestation unit tests, 5 attestation API integration tests, and /verify tests (valid round-trip, tamper rejection, missing-field 422).

## Deferred

## Out of Scope

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 |  | validated | none | none | S01 delivers deep pipeline: README content via REST API (get_repo_readme), CI/CD config detection (get_repo_cicd_configs covering 11 well-known path patterns), contribution calendar via GraphQL (get_user_contributions), commit message semantics analysis, and AI usage pattern detection. All 12 signals (8 original + 4 new) extracted and scored. Incremental freshness via CrawlCache with pushed_at comparison. 69/69 tests pass. |
| R002 | core-capability | validated | none | none | S02 delivers role-adaptive scoring: 3 built-in profiles (engineering, marketing, non-technical) with distinct signal weights and per-signal confidence thresholds. ScoreResult.details includes profile_name and signals_below_threshold. /profiles endpoint exposes available profiles. /score?role=marketing returns different scores than default. Signals below confidence threshold excluded with proportional weight redistribution. 129/129 tests pass including 22 role-adaptive/profile-specific tests and 36 API tests covering all three endpoints. |
| R003 | core-capability | validated | none | none | S03 delivers full Ed25519 attestation pipeline: sign_score, verify_attestation, and load_or_generate_signing_key in attest/ module; attestation blocks (signature, public_key, signed_payload, signed_at) in /score and /match responses via _build_attestation helper; POST /verify endpoint for third-party verification returning {valid, payload, error}; graceful degradation: omitted attestation block + warning log when key is unavailable. 161 tests pass including 18 attestation unit tests, 5 attestation API integration tests, and /verify tests (valid round-trip, tamper rejection, missing-field 422). |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 3 (R001, R002, R003)
- Unmapped active requirements: 0
