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

**M002 complete.** Rust scoring library ports all 12 signals with zero-diff exact match against the Python reference, validated via dedicated cross-comparison crate (scoring-cross-compare) across 3 fixtures. SP1 zkVM proving pipeline is code-complete: no_std scoring-sp1-core, guest program, host script (local CPU + Succinct Prover Network), and Python prover CLI wrapper. SP1Verifier.sol Groth16 verifier contract compiled (2294 bytes, solc 0.8.28 viaIR) with VKey registry for multi-program support, deploy script and deterministic wallet ready. Async Celery/Redis proof queue wired into /score endpoint with 3-retry exponential backoff, jitter, and at-least-once delivery. GET /proof/{username}/status endpoint tracks full lifecycle (pending → proof_generating → proof_generated → on_chain → failed). Ed25519 attestation always returned immediately — ZK proving failure never blocks users. 286+ tests pass. CI pipeline (3-stage: Rust SP1 → Python → Contracts) configured for ubuntu-latest.

**Note:** Two M002 success criteria have environmental gaps — SP1 cargo prove build requires Linux/macOS (CI pipeline on ubuntu-latest), and SP1Verifier.sol contract deployment needs ~0.01 Base Sepolia ETH for wallet funding. Both are code-complete and documented; neither requires remediation slices.

Candidate profile pages, recruiter marketplace, ZK proof viewer, and matchmaking are not yet built.

## Architecture / Key Patterns

- **Crawl layer:** Python (FastAPI + aiohttp/requests) — fetches GitHub data via dual API strategy: GraphQL for structured data (profile, contributions, repos), REST for file contents (READMEs, CI/CD configs). Incremental caching via CrawlCache.
- **Scoring layer (reference):** Python — 12 behavioral signals with role-adaptive weights.
- **Scoring layer (ZK/proved):** Rust — scoring-types (shared data), scoring-core (std engine + profiles), scoring-sp1-core (no_std engine for RISC-V), scoring-cli (CLI), scoring-cross-compare (zero-diff CI gate).
- **Attestation layer:** Ed25519 — deterministic canonical JSON signing. Every score carries an independently verifiable signature. Graceful degradation when signing key is unavailable.
- **Proving layer:** SP1 zkVM — no_std scoring-sp1-core proven in RISC-V guest. Async — Ed25519 attestation serves as instant fallback. SP1_PROVER env var switches between local CPU and Succinct Prover Network.
- **Verification layer:** Base L2 — SP1Verifier.sol (Groth16 verifier contract) with VKey registry for multi-program support. ~$0.008/proof verification cost. Deploy script and deterministic wallet ready.
- **Async queue:** Celery with Redis — proof generation tasks with 3-retry exponential backoff, jitter, acks_late + reject_on_worker_lost. Proof lifecycle tracked via in-memory ProofStatusStore (thread-safe singleton, upgradable to Redis).
- **Data layer:** JSON-per-user CrawlCache for incremental crawl freshness. (Future: PostgreSQL for attestations, profiles, user state, recruiter data.)
- **Frontend:** Thin web UI — crawl→score→attest→verify flow. (Future: candidate profile pages, recruiter dashboard, ZK proof viewer.)
- **Wallet abstraction (future):** Invisible wallet for non-crypto users (Web3Auth/Privy-like pattern).

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] **M001: Deep Pipeline & Attested Scores** — Deep GitHub mining, role-adaptive scoring, Ed25519 attestation. Shippable standalone. ✓ Complete
- [x] **M002: ZK Proving Layer** — Rust scoring lib, SP1 prover pipeline, Base verifier contract. Async proving with Ed25519 fallback. ✓ Complete
- [ ] M003: Candidate Profile & Sharing — Shareable profile pages, ZK proof viewer, wallet abstraction, GitHub opt-in/notifications.
- [ ] M004: Recruiter Dashboard & Marketplace — Search/filter, budget/scope tiers, pay-per-verification pricing.
- [ ] M005: Matchmaking & Notifications — Automated candidate-role matching, employer-initiated interview requests via GitHub.
