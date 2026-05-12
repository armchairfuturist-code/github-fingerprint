# GitHub Fingerprint

## What This Is

A ZK-verified skill fingerprint platform. Candidates connect their GitHub, get a deep multifactor analysis of their code, and share a cryptographically verifiable profile with recruiters. Recruiters pay to verify candidates at varying depth tiers. No timed coding tests, no keyword-stuffed resumes — just proven work history with zero-knowledge proof that the score was computed honestly.

## Core Value

A portable, cryptographically verifiable credential that lets any GitHub user prove their skills to employers without timed coding tests, manual portfolio reviews, or exposing more data than they want.

## Project Shape

- **Complexity:** complex
- **Why:** Multi-domain (ZK proving, blockchain L2, GitHub API pipeline, marketplace economics) with deep technical unknowns in the ZK proving layer.

## Current State

**M001 complete.** Deep GitHub mining pipeline delivers README content, CI/CD detection, contribution calendar analysis, commit semantics, and AI usage patterns. Role-adaptive scoring engine supports engineering, marketing, and non-technical profiles with configurable signal weights and confidence thresholds. Every score carries an independently verifiable Ed25519 signature with a /verify endpoint for third-party authentication. Full end-to-end frontend: enter username → deep crawl → score → attest → share. Returning users benefit from incremental CrawlCache (pushed_at-based stale detection). 198 tests pass covering crawler, scoring, profiles, attestation, API, and integration.

The ZK proving layer (Rust scoring lib → SP1 prover → Base verifier), candidate profile pages, recruiter marketplace, and ZK proof viewer are not yet built.

## Architecture / Key Patterns

- **Crawl layer:** Python (FastAPI + aiohttp/requests) — fetches GitHub data via dual API strategy: GraphQL for structured data (profile, contributions, repos), REST for file contents (READMEs, CI/CD configs). Incremental caching via CrawlCache.
- **Scoring layer:** Python — 12 behavioral signals with role-adaptive weights. (Future: ported to Rust for SP1 zkVM provability.)
- **Attestation layer:** Ed25519 — deterministic canonical JSON signing. Every score carries an independently verifiable signature. Graceful degradation when signing key is unavailable.
- **Proving layer (future):** SP1 zkVM — proves the Rust scoring function executed correctly. Asynchronous — Ed25519 attestation serves as instant fallback.
- **Verification layer (future):** Base L2 — Solidity verifier contract. ~$0.008/proof verification cost.
- **Data layer:** JSON-per-user CrawlCache for incremental crawl freshness. (Future: PostgreSQL for attestations, profiles, user state, recruiter data.)
- **Frontend:** Thin web UI — crawl→score→attest→verify flow. (Future: candidate profile pages, recruiter dashboard, ZK proof viewer.)
- **Wallet abstraction (future):** Invisible wallet for non-crypto users (Web3Auth/Privy-like pattern).

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] **M001: Deep Pipeline & Attested Scores** — Deep GitHub mining, role-adaptive scoring, Ed25519 attestation. Shippable standalone. ✓ Complete
- [ ] M002: ZK Proving Layer — Rust scoring lib, SP1 prover pipeline, Base verifier contract. Async proving with Ed25519 fallback.
- [ ] M003: Candidate Profile & Sharing — Shareable profile pages, ZK proof viewer, wallet abstraction, GitHub opt-in/notifications.
- [ ] M004: Recruiter Dashboard & Marketplace — Search/filter, budget/scope tiers, pay-per-verification pricing.
- [ ] M005: Matchmaking & Notifications — Automated candidate-role matching, employer-initiated interview requests via GitHub.
