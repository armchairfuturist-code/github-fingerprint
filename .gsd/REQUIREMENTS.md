# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R001 — Deep GitHub Mining
- Class: core-capability
- Status: active
- Description: The system must crawl GitHub user data via GraphQL API — repos, commits, issues, PRs, README content, contribution graphs, CI/CD indicators, commit message semantics, AI usage patterns.
- Why it matters: The quality of the fingerprint depends entirely on the depth and breadth of data collected. Surface-level stats miss what makes a developer's work unique.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02
- Validation: unmapped
- Notes: Must include incremental freshness — returning users only fetch data pushed since last crawl.

### R002 — Role-Adaptive Scoring
- Class: differentiator
- Status: active
- Description: The scoring engine must produce role-adaptive scores — different signal weights for engineering roles vs marketing roles vs non-technical roles. The algorithm iterates based on job type learnings.
- Why it matters: A marketing role values different signals (documentation, communication, tool diversity) than an engineering role (CI/CD depth, code complexity, PR patterns). One-size scoring misses the point.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Algorithm will iterate heavily. The Rust port for ZK proving must handle weight updates without circuit redeployment.

### R003 — Ed25519 Attestation
- Class: continuity
- Status: active
- Description: Every score must be cryptographically signed with Ed25519 so anyone can independently verify the server attested to it. Extend existing attestation to cover new signals.
- Why it matters: The Phase 1 trust model. Before ZK proofs exist, the Ed25519 signature is the verifiable link between the server and the score.
- Source: execution
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: partial
- Notes: Already implemented for the initial 8 signals. Needs extension to cover new deep pipeline signals.

### R004 — ZK Proving Pipeline (SP1)
- Class: core-capability
- Status: active
- Description: The scoring function must be provable via SP1 zkVM, producing a zero-knowledge proof that the score was computed correctly from the input data. Scoring function written in Rust.
- Why it matters: Trustless verification. Recruiters don't need to trust the server — they verify the math. This is the key differentiator vs every existing GitHub scoring tool.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: unmapped
- Notes: Scoring logic compiled to RISC-V via Rust, proven by SP1 Hypercube, output is a STARK proof compressed to Groth16 for on-chain verification.

### R005 — Base L2 Verifier Contract
- Class: integration
- Status: active
- Description: A Solidity verifier contract deployed on Base L2 that validates SP1 proofs of the scoring function.
- Why it matters: On-chain verification makes the attestation publicly checkable without running any custom software. Anyone with an RPC endpoint can verify.
- Source: inferred
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Verification cost ~$0.008/proof on Base. SP1 provides verifier contract templates.

### R006 — Async Proving with Fallback
- Class: quality-attribute
- Status: active
- Description: The ZK proving pipeline must be asynchronous. Users get their profile immediately with Ed25519 attestation. The ZK proof upgrades the attestation async. If proving fails at any point, Ed25519 attestation remains valid.
- Why it matters: Users should never experience proving latency. The Ed25519 attestation is always the baseline trust model. ZK is an upgrade, not a gate.
- Source: inferred
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Queue-based proving pipeline. Polling endpoint for status. Webhook notification when proof is ready.

### R007 — Candidate Profile Page
- Class: primary-user-loop
- Status: active
- Description: Users must get a shareable profile link with their attested scores, signal breakdown, proof status, and ZK verification badge.
- Why it matters: The profile is the product. It's what candidates share with recruiters. It must be instantly useful, visually clear, and cryptographically verifiable.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Thin UI — the data and proof are the value, not the design.

### R008 — Wallet Abstraction
- Class: launchability
- Status: active
- Description: Non-crypto users must be able to use the platform without managing wallets directly. Wallets are created implicitly as "data backpacks" with zero cost to individuals.
- Why it matters: If users need to install Metamask, adoption dies. The UX must be as simple as "enter username, get your link."
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Web3Auth / Privy / Dynamic pattern. Gas fees shouldered by recruiters.

### R009 — Recruiter Search & Filter
- Class: primary-user-loop
- Status: active
- Description: Recruiters must be able to search and filter candidates by skill signals, role type, budget, and verification depth tier.
- Why it matters: Recruiters need to find candidates efficiently. The search is the revenue surface.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Candidates who opted in are discoverable. Opt-in status tied to wallet/data backpack.

### R010 — Pay-per-Verification
- Class: launchability
- Status: active
- Description: Recruiters pay for verification depth tiers. Higher tiers = deeper analysis + ZK proof. Individuals always free.
- Why it matters: Free for candidates drives adoption. Recruiter revenue sustains the platform. Tiered pricing captures willingness to pay for deeper analysis.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Gas costs included in tier pricing. Premium tiers get priority proving queue, deeper signal analysis, faster turnaround.

### R011 — Matchmaking & Notifications
- Class: primary-user-loop
- Status: active
- Description: When a recruiter expresses interest in a candidate, the candidate receives a notification via GitHub (issue comment or similar mechanism).
- Why it matters: The thesis is that great candidates aren't actively looking. Passive discovery + low-friction notification opens the door without cold outreach.
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: none
- Validation: unmapped
- Notes: GitHub notification via API (create issue on a designated repo, or use GitHub notifications API). Email fallback.

## Validated

### R012 — GitHub GraphQL Crawl
- Class: core-capability
- Status: validated
- Description: Crawler fetches user profile, repos, commits, issues, and PRs via GitHub GraphQL API with rate limit handling and automatic retry.
- Why it matters: Foundation for all analysis.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `crawler/github_api.py` works in production.

### R013 — 8-Signal Extraction
- Class: core-capability
- Status: validated
- Description: Extract commit_consistency, language_diversity, issue_engagement, pr_patterns, project_ownership, review_patterns, response_time, and readme_quality from raw GitHub data.
- Why it matters: Core behavioral analysis.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `signals/extractor.py` implements all eight with scoring 0-100 and confidence metrics.

### R014 — Weighted Scoring Engine
- Class: core-capability
- Status: validated
- Description: Configurable weighted-average scoring with risk flag generation from signal scores.
- Why it matters: Core scoring mechanism.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `scoring/engine.py` with 8 default weights summing to 1.0.

### R015 — HTTP API Layer
- Class: core-capability
- Status: validated
- Description: FastAPI service with /health, /score (POST+GET), /match (POST+GET), /verify endpoints.
- Why it matters: Public API surface.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `api/main.py` serves all endpoints with pydantic models.

### R016 — Web Frontend
- Class: launchability
- Status: validated
- Description: Dark-themed monospace UI with GitHub username + role description input that hits the /match endpoint.
- Why it matters: Working demo surface for the MVP.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `index.html` — will be superseded by candidate profile pages.

### R017 — Test Suite
- Class: quality-attribute
- Status: validated
- Description: pytest coverage for crawler data classes, GraphQL client mocking, and scoring engine with mock data.
- Why it matters: Regression protection.
- Source: execution
- Primary owning slice: none
- Supporting slices: none
- Validation: validated
- Notes: Existing `tests/test_crawler.py` and `tests/test_scoring.py`.

## Deferred

### R018 — Multi-Chain Verification
- Class: integration
- Status: deferred
- Description: Deploy the ZK verifier contract to additional L2s (Arbitrum, Optimism) beyond Base.
- Why it matters: Recruiters who prefer other chains can verify without bridging.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Defer until Base deployment is stable and we have recruiter demand for other chains.

### R019 — Local Prover Fallback
- Class: operability
- Status: deferred
- Description: Run SP1 proving on local GPU hardware as backup when prover network is unavailable.
- Why it matters: Independence from prover network availability.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Defer until paying recruiters exist and proving costs justify the hardware investment.

## Out of Scope

### R020 — Native Mobile Apps
- Class: anti-feature
- Status: out-of-scope
- Description: No native iOS or Android applications. Web-first by design.
- Why it matters: Heavy UX is secondary when agents and notifications drive the workflow.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The thesis is that agents and GitHub-native notifications replace the need for app stores.

### R021 — Full On-Chain Identity
- Class: anti-feature
- Status: out-of-scope
- Description: No full self-sovereign identity system. Wallets are abstracted and invisible to end users.
- Why it matters: Wallet abstraction removes crypto friction. Full SSI is a later concern.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The data backpack pattern gives users portable credentials without requiring crypto literacy.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | active | M001/S01 | M001/S02 | mapped |
| R002 | differentiator | active | M001/S02 | none | mapped |
| R003 | continuity | active | M001/S03 | none | partial |
| R004 | core-capability | active | M002/S01 | M002/S02 | mapped |
| R005 | integration | active | M002/S02 | none | mapped |
| R006 | quality-attribute | active | M002/S03 | none | mapped |
| R007 | primary-user-loop | active | M003/S01 | none | mapped |
| R008 | launchability | active | M003/S02 | none | mapped |
| R009 | primary-user-loop | active | M004/S01 | none | mapped |
| R010 | launchability | active | M004/S02 | none | mapped |
| R011 | primary-user-loop | active | M005/S01 | none | mapped |
| R012 | core-capability | validated | — | — | validated |
| R013 | core-capability | validated | — | — | validated |
| R014 | core-capability | validated | — | — | validated |
| R015 | core-capability | validated | — | — | validated |
| R016 | launchability | validated | — | — | validated |
| R017 | quality-attribute | validated | — | — | validated |
| R018 | integration | deferred | none | none | unmapped |
| R019 | operability | deferred | none | none | unmapped |
| R020 | anti-feature | out-of-scope | none | none | n/a |
| R021 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 11
- Mapped to slices: 11
- Validated: 6
- Unmapped active requirements: 0
