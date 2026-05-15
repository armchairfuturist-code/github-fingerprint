---
id: M001
title: "Deep Pipeline & Attested Scores"
status: complete
completed_at: 2026-05-12T06:59:51.851Z
key_decisions:
  - Dual API strategy: GraphQL for structured data (profile, contributions, repos), REST for file contents (READMEs, CI/CD configs)
  - CrawlCache with pushed_at-based staleness detection for incremental returning-user crawls
  - RoleProfile validation at construction time via __post_init__ (weights sum to 1.0, all signals present, thresholds in [0,1])
  - Backward compatibility: resolve_role_profile(None) returns engineering; default constructor uses legacy flat weights
  - Ed25519 canonical JSON (sorted keys, no extra whitespace) for cross-platform payload consistency
  - Lazy GITHUB_TOKEN initialization via _get_github_client() on first use instead of module import time
  - Integration tests with SimpleNamespace mock objects matching GitHub dataclass shapes
key_files:
  - crawler/github_api.py
  - signals/extractor.py
  - scoring/engine.py
  - scoring/profiles.py
  - attest/__init__.py
  - attest/config.py
  - attest/signer.py
  - api/main.py
  - index.html
  - tests/test_crawler.py
  - tests/test_scoring.py
  - tests/test_api.py
  - tests/test_attest.py
  - tests/test_integration.py
lessons_learned:
  - Module-level GITHUB_TOKEN validation breaks pytest test collection — defer to lazy factory function instead.
  - Stateful ScoringEngine singleton requires careful integration test design (avoid cross-test assertions on mutable state).
  - REST and GraphQL GitHub APIs need separate base URLs, auth mechanisms, and response parsers (cannot share infrastructure without careful abstraction).
  - Prefer SimpleNamespace mock objects over real HTTP calls for integration tests — keeps tests fast and deterministic.
  - Ed25519 canonical JSON must use sorted keys and no extra whitespace for cross-platform verification compatibility.
---

# M001: Deep Pipeline & Attested Scores

**Built the deep GitHub mining pipeline, role-adaptive scoring engine with 3 profiles, Ed25519 attestation on every score, and a full end-to-end crawl→score→attest→verify→share frontend.**

## What Happened

M001 delivered the full deep GitHub fingerprint pipeline across 4 slices. S01 extended the MVP crawler with REST-based README fetching, GraphQL contribution calendar analysis, CI/CD config detection across 11 well-known paths, commit semantics analysis, AI usage pattern detection, and a CrawlCache for incremental returning-user crawls (pushed_at-based staleness detection reduces API calls >80%). S02 transformed the flat-weight scoring engine into a role-adaptive system with 3 built-in profiles (engineering, marketing, non-technical), per-signal confidence thresholds with proportional weight redistribution, a /profiles API endpoint, and two-tier profile matching in /match. S03 implemented full Ed25519 attestation with a canonical JSON signing module, attestation blocks in /score and /match responses, a POST /verify endpoint for third-party verification, and graceful degradation when no signing key is configured. S04 wired everything together: deferred GITHUB_TOKEN validation to lazy initialization (fixing a testability blocker), 37 end-to-end integration tests with SimpleNamespace mock objects, a full frontend with Score/Match tabs, role selector, signal breakdown bars, attestation copy-to-clipboard, and responsive dark-monospace UI. The complete regression suite runs 198 tests in 0.31s with zero failures.

## Success Criteria Results

### Success Criteria Verification

| Criterion | Verification | Status |
|---|---|---|
| S01: Crawler fetches README content, detects CI/CD configs, analyzes commit patterns, and caches results for incremental updates | get_repo_readme() REST API with base64 decoding + markdown structure parsing; get_repo_cicd_configs() checking 11 well-known paths; get_user_contributions() GraphQL with streak analysis; CrawlCache with pushed_at staleness detection. 69/69 tests pass. | ✅ Passed |
| S02: Scoring engine supports multiple role profiles with different signal weights | 3 built-in RoleProfile instances (engineering, marketing, non-technical) with distinct 12-signal weights summing to 1.0. Confidence threshold filtering + proportional weight redistribution. /profiles endpoint for discovery. 129/129 tests pass. | ✅ Passed |
| S03: Every score carries an independently verifiable Ed25519 signature covering all signals | attest/ module with sign_score, verify_attestation, load_or_generate_signing_key. Attestation blocks in /score and /match responses. POST /verify endpoint. Graceful degradation on missing key. 161/161 tests pass. | ✅ Passed |
| S04: Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates | Frontend with Score/Match tabs, role selector, signal breakdown, attestation copy-to-clipboard. 37 integration tests covering complete pipeline. 198/198 tests pass. GITHUB_TOKEN lazy init enables clean imports. | ✅ Passed |

## Definition of Done Results

### Definition of Done Verification

| Item | Status |
|---|---|
| All 4 slices [x] complete | ✅ gsd_milestone_status: S01=S04 all complete |
| Slice summaries exist | ✅ All 4 SUMMARY.md files present and verified |
| Cross-slice integration works | ✅ S04 integration test suite (37 tests) covers end-to-end crawl→score→attest→verify |
| 198 tests pass | ✅ 198 passed, 0 failed, 0 errors in 0.31s |
| GITHUB_TOKEN import fix | ✅ Module imports without env var; tests pass without GITHUB_TOKEN |

## Requirement Outcomes

### Requirement Outcomes

| ID | Status | Evidence |
|---|---|---|
| R001 — Deep GitHub Mining | Validated | S01 delivers deep pipeline: README content via REST, CI/CD config detection (11 paths), contribution calendar via GraphQL, commit semantics, AI pattern analysis, CrawlCache. 69/69 tests pass. |
| R002 — Role-Adaptive Scoring | Validated | S02 delivers 3 profiles with distinct weights, confidence threshold filtering, weight redistribution, /profiles endpoint. 129/129 tests pass including 22 role-adaptive tests. |
| R003 — Score Attestation | Validated | S03 delivers Ed25519 signing, /verify endpoint, attestation blocks in /score and /match, graceful degradation. 161/161 tests pass including 18 attestation unit tests. |

## Deviations

None. All slices delivered as specified in the roadmap with no scope changes.

## Follow-ups

Fix api/main.py to defer GITHUB_TOKEN validation to FastAPI lifespan startup for cleaner architecture (currently uses module-level lazy function which is an improvement but not ideal). The ZK proving layer (M002), candidate profiles (M003), recruiter dashboard (M004), and matchmaking (M005) remain for future milestones.
