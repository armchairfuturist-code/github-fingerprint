# GitHub Fingerprint

## What This Is

A ZK-verified skill fingerprint platform. Candidates connect their GitHub, get a deep multifactor analysis of their code, and share a cryptographically verifiable profile with recruiters. Recruiters pay to verify candidates at varying depth tiers. No timed coding tests, no keyword-stuffed resumes — just proven work history with zero-knowledge proof that the score was computed honestly.

## Core Value

A portable, cryptographically verifiable credential that lets any GitHub user prove their skills to employers without timed coding tests, manual portfolio reviews, or exposing more data than they want.

## Project Shape

- **Complexity:** complex
- **Why:** Multi-domain (ZK proving, blockchain L2, GitHub API pipeline, marketplace economics) with deep technical unknowns in the ZK proving layer.

## Current State

MVP exists with FastAPI backend, GitHub GraphQL crawler, 8 behavioral signals, weighted scoring engine, Ed25519 cryptographic attestations, role keyword matching, and a web frontend. Test suite covers crawler and scoring engine. The ZK proving layer, candidate profiles, recruiter marketplace, and deep signal mining are not yet built.

## Architecture / Key Patterns

- **Crawl layer:** Python (existing FastAPI + aiohttp/requests) — fetches GitHub GraphQL data
- **Scoring layer:** Rust — ported from Python for SP1 zkVM provability. Role-adaptive weights.
- **Proving layer:** SP1 zkVM — proves the Rust scoring function executed correctly. Asynchronous — Ed25519 attestation serves as instant fallback.
- **Verification layer:** Base L2 — Solidity verifier contract. ~$0.008/proof verification cost.
- **Data layer:** PostgreSQL — attestations, profiles, user state, recruiter data. Crawl cache for incremental freshness.
- **Frontend:** Thin web UI — candidate profile pages, recruiter dashboard, ZK proof viewer.
- **Wallet abstraction:** Invisible wallet for non-crypto users (Web3Auth/Privy-like pattern).

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Deep Pipeline & Attested Scores — Deep GitHub mining, role-adaptive scoring, Ed25519 attestation. Shippable standalone.
- [ ] M002: ZK Proving Layer — Rust scoring lib, SP1 prover pipeline, Base verifier contract. Async proving with Ed25519 fallback.
- [ ] M003: Candidate Profile & Sharing — Shareable profile pages, ZK proof viewer, wallet abstraction, GitHub opt-in/notifications.
- [ ] M004: Recruiter Dashboard & Marketplace — Search/filter, budget/scope tiers, pay-per-verification pricing.
- [ ] M005: Matchmaking & Notifications — Automated candidate-role matching, employer-initiated interview requests via GitHub.
