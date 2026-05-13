# GitHub Fingerprint

> **From GitHub activity to ZK-proven skill profile in one click.**
> No timed coding tests. No keyword-stuffed resumes. Just proven work history, cryptographically verified.

[![Tests](https://img.shields.io/badge/tests-319_passing-brightgreen.svg)](#)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](#)
[![Rust](https://img.shields.io/badge/rust-1.80+-orange.svg)](#)
[![SP1](https://img.shields.io/badge/zkVM-SP1-purple.svg)](#)
[![Base L2](https://img.shields.io/badge/verifier-Base_L2-blueviolet.svg)](#)

---

## The Product

A portable, cryptographically verifiable credential that lets **any GitHub user** prove their skills to employers — without timed tests, manual portfolio reviews, or exposing more data than they want.

**For candidates:** Enter your GitHub username → get a deep multi-factor analysis of your code → claim your shareable profile → prove it's real with an independently verifiable signature.

**For recruiters:** Verify candidates at glance. No more "trust me bro" resumes. Every score carries a cryptographic attestation you can verify yourself. Coming soon: pay-per-verification with ZK proof verification on-chain.

---

## Features (MVP Complete)

| What | How | Status |
|------|-----|--------|
| **Deep GitHub Mining** | GraphQL + REST pipeline — README content, CI/CD configs, contribution calendars, commit semantics, AI usage | Done |
| **Role-Adaptive Scoring** | 12 behavioral signals, 3 profiles (engineering/marketing/non-technical), confidence thresholds | Done |
| **Ed25519 Attestation** | Every score independently verifiable via /verify — instant cryptographic trust | Done |
| **ZK Proving Pipeline** | Rust scoring lib, SP1 zkVM guest, Groth16 verifier on Base L2. Async with Ed25519 fallback | Done |
| **Shareable Profile Pages** | Server-rendered /u/{username} — score ring, signal bars, attestation badge, proof status | Done |
| **One-Click Analysis** | Enter username, watch the crawl, get your profile. Progress overlay with live status | Done |
| **Wallet Abstraction** | Implicit Privy wallet created on first analysis — no seed phrases, no browser extensions | Done |
| **ZK Proof Viewer** | Expandable proof badge with metadata, status, and one-click copy to clipboard | Done |
| **Proof Queue** | Celery/Redis async proof generation with 3-retry exponential backoff | Done |

**319 tests passing** across crawler, scoring, attestation, API, profile pages, Celery tasks, SP1 proving, and wallet.

---

## How It Works

```
GitHub -> Deep Crawl -> 12 Signals -> Score -> Attestation -> Profile
                  |                                                |
                  +-- (Async) -> SP1 zkVM -> Groth16 -> Base L2 -> Proof Badge
                                                                   |
                                            Wallet (Privy) <--------+
```

1. **Crawl** — Your public GitHub profile, repos, commits, issues, PRs, READMEs, CI/CD configs, contribution calendar, and commit messages are analyzed through a dual GraphQL/REST pipeline.

2. **Score** — 12 behavioral signals are extracted and scored against a role-adaptive profile (engineering, marketing, or non-technical). Signals below confidence thresholds are excluded with proportional weight redistribution.

3. **Attest** — Every score is immediately signed with an Ed25519 key. Returned in the response. Anyone can verify at /verify — no server trust required.

4. **Profile** — A shareable, server-rendered profile page at /u/{username} displays your overall score, signal breakdown, attestation status, and ZK proof status.

5. **Prove (Async)** — SP1 zkVM generates a zero-knowledge proof of the scoring computation in the background. Verified on Base L2 (~$0.008/proof). Ed25519 attestation serves as instant fallback.

6. **Wallet** — An embedded Privy wallet is created on first analysis (no seed phrases). Stores attestation hashes in your data backpack for future on-chain verification.

---

## Quick Start

```bash
pip install -r requirements.txt
export GITHUB_TOKEN="ghp_your_token_here"
python -m api.main
```

Open http://localhost:8000 -> enter a GitHub username -> get your verifiable skill profile.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /score | Score a GitHub user (full JSON body) |
| GET | /score/{username} | Score via GET (?role= & ?weights=) |
| POST | /match | Match user to role description |
| GET | /match/{username} | Match via GET (?role=...) |
| POST | /verify | Verify an Ed25519 attestation signature |
| GET | /profiles | List available role profiles with weights |
| GET | /proof/{username}/status | Check ZK proof generation status |
| GET | /wallet/{username}/status | Check wallet creation status |
| GET | /u/{username} | Shareable candidate profile page (SSR) |

---

## Signals (12 Behavioral Dimensions)

| Signal | Measures | Proxies For |
|--------|----------|-------------|
| commit_consistency | Commit cadence regularity | Work ethic, persistence |
| language_diversity | Programming language range | Adaptability |
| issue_engagement | Issue participation & close rate | Collaborative debugging |
| pr_patterns | PR size balance & merge rate | Code quality |
| project_ownership | Owned vs forked repo ratio | Initiative |
| review_patterns | Review comment participation | Technical communication |
| response_time | Time to merge/close | Velocity |
| readme_quality | Repo description quality | Documentation habits |
| commit_semantics | Commit message structure | Communication clarity |
| cicd_maturity | Workflow configs & automation | Engineering discipline |
| contribution_consistency | Calendar regularity | Sustained effort |
| ai_usage_patterns | Commit timing & message style | AI-augmented development

Scores are role-adaptive — engineering weights code signals higher, marketing weights communication signals higher, non-technical weights project ownership higher.

---

## Milestones

- [x] **M001: Deep Pipeline & Attested Scores** — Deep GitHub mining, 12-signal role-adaptive scoring, Ed25519 attestation, /verify endpoint.
- [x] **M002: ZK Proving Layer** — Rust scoring lib (zero-diff vs Python), SP1 zkVM, Base L2 verifier contract (2294 bytes).
- [x] **M003: Candidate Profile & Sharing** — Profile pages at /u/{username}, opt-in crawl flow, Privy wallet abstraction, ZK proof viewer.
- [ ] M004: Recruiter Dashboard & Marketplace
- [ ] M005: Matchmaking & Notifications

---

## Technical Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Crawl** | Python (FastAPI + aiohttp/requests) | GitHub GraphQL + REST data pipeline, incremental CrawlCache |
| **Scoring (ref)** | Python | 12 behavioral signals, role-adaptive profiles, confidence thresholds |
| **Scoring (proved)** | Rust (no_std, RISC-V) | Exact-match port for SP1 zkVM, cross-validated vs Python |
| **Attestation** | Ed25519 (PyNaCl/libsodium) | Instant cryptographic signature on every score |
| **Proving** | SP1 zkVM (Succinct) | Zero-knowledge proof of scoring computation |
| **Verification** | Solidity (Base L2) | SP1Verifier.sol Groth16 verifier, ~$0.008/proof |
| **Async Queue** | Celery + Redis | Background proof generation, 3-retry exponential backoff |
| **Wallet** | Privy REST API | Implicit embedded wallet creation, data backpack |
| **Frontend** | Jinja2 (SSR) + CSS | Dark-themed profile pages, progress overlay, proof viewer |
| **Tests** | pytest (Python) + cargo test (Rust) | 319+ tests across all layers |

Key architecture decisions: **SP1 zkVM** over circuit DSLs (D001), **Base L2** for lowest verification cost (D002), **Async proving with Ed25519 fallback** (D003), **Role-adaptive scoring** (D004), **Privy** wallet abstraction (D012).

See [.gsd/DECISIONS.md](.gsd/DECISIONS.md) for the full register.


## Development

```bash
python -m pytest tests/ -v     # Full test suite (319 tests)
uvicorn api.main:app --reload  # Dev server with hot reload
```

Requirements: Python 3.12+, Rust 1.80+, Redis (for Celery proof queue).

Read the full architecture decisions in .gsd/DECISIONS.md.

---

*Your code is your resume. Match people to meaningful work through their open-source fingerprint.*
