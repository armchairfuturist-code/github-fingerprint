# GitHub Fingerprint

> **From GitHub activity to ZK-proven skill profile. No trust required.**
> No timed coding tests. No keyword-stuffed resumes. Just proven work history, cryptographically verified.

[![Tests](https://img.shields.io/badge/tests-319_passing-brightgreen.svg)](#)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](#)
[![Rust](https://img.shields.io/badge/rust-1.80+-orange.svg)](#)
[![SP1](https://img.shields.io/badge/zkVM-SP1-purple.svg)](#)
[![Base L2](https://img.shields.io/badge/verifier-Base_L2-blueviolet.svg)](#)

---

## The Resume Is Broken

A bad hire who 'signals AI knowledge' costs $50K+ before you catch it. Resumes are AI-generated, screened by AI, and tell you nothing about whether someone can actually *build*. It's a circular economy of fiction.

Meanwhile, every developer leaves a verifiable trail: commits, PRs, issues, documentation, CI/CD maturity. Your GitHub tells the real story. GitHub Fingerprint is the proof layer — 12 behavioral signals, cryptographically attested, independently verifiable. No trust in the platform required.

**Everyone else asks you to trust their score. GitHub Fingerprint lets you prove it.**

---

## How We're Different

| Feature | GitHub Fingerprint | GitRoll | BuilderGraph | Others |
|---------|--------------------|---------|--------------|--------|
| GitHub profile scoring | 12 behavioral signals | CURISM score (proprietary) | 7 factors | Basic composite |
| Role-adaptive scoring | Engineering / Marketing / Non-tech | Unclear | No | No |
| **ZK proof of computation** | **SP1 zkVM + Groth16 on Base L2** | No | No | No |
| **Cryptographic attestation** | **Ed25519 (instant fallback)** | No | No | No |
| **On-chain verification** | **Yes (~$0.008/proof)** | No | Storage only (DKG) | No |
| AI usage pattern detection | Yes (12th signal) | No | No | No |
| No OAuth needed | Just a username | No | No | Varies |
| Shareable profile page | SSR at /u/{username} | Agentic AI profile | DKG-based | No |

**GitHub Fingerprint is the only platform where a recruiter can verify the scoring computation itself — on-chain, in seconds, without trusting the server.**

---

## 12 Signals

What the 12 signals measure, how they're scored, and how they form the complete engineering fingerprint.

| # | Signal | Description | Weight |
|---|--------|-------------|--------|
| 1 | **Repo Portfolio** | Breadth of created repos (engineering, docs, config) | 12 |
| 2 | **Code Consistency** | Regular commit cadence over 90-day window | 11 |
| 3 | **Code Collaboration** | # of co-authored PRs across teams | 10 |
| 4 | **Code Review** | PRs reviewed (commented, approved, requested changes) | 10 |
| 5 | **Issue Discovery** | Issues created (+bugs found in own/others repos) | 9 |
| 6 | **Issue Resolution** | Issues closed (PRs linked, stale tagging) | 9 |
| 7 | **Context Awareness** | Documentation coverage (PR bodies, issues, wiki) | 8 |
| 8 | **Reach and Impact** | Stars, forks, watchers across projects | 8 |
| 9 | **Maintainer Trust** | Explicit repo permissions (collaborator/owner) | 7 |
| 10 | **Community Engagement** | Comments on issues, PRs, discussions | 7 |
| 11 | **CI/CD Maturity** | Workflow files, test coverage, deployment configs | 5 |
| 12 | **AI Usage Detection** | AI-generated commit patterns (AI-only or hybrid) | 4 |

**Total: 100** — Normalised to 0–100 scale.

---

## How It Works

```
                    ┌──────────────────────────────────────────────┐
                    │        GitHub Fingerprint Architecture        │
                    └──────────────────────────────────────────────┘
┌──────────┐    ┌────────────────────┐    ┌─────────────────────────┐
│          │    │                    │    │                         │
│  GitHub  │───>│  Score Engine      │───>│  Attestation Layer      │
│  API     │    │  (12 signals,      │    │  (Ed25519 / SP1 zkVM)   │
│          │    │   role-adaptive)   │    │                         │
└──────────┘    └────────────────────┘    └─────────────────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │                  │
                                          │  Verifier        │
                                          │  (on-chain /     │
                                          │   offline)       │
                                          │                  │
                                          └──────────────────┘
```


**1. Score** — The Score Engine pulls public GitHub data, computes 12 weighted signals, applies role-adaptive normalization, and produces a single 0–100 fingerprint score.

**2. Attest** — The Attestation Layer wraps the score into a structured attestation payload, optionally proving computation integrity via SP1 zkVM (Groth16, ~$0.008/proof on Base L2). Instant fallback to Ed25519 signing.

**3. Verify** — Anyone can verify the attestation: on-chain via the deployed smart contract on Base L2, or offline by re-running the scorer and checking the signature. No trust required.

---

## Signals Deep Dive

### 1. Repo Portfolio (Weight: 12)

Measures the breadth of repositories created by the developer — not just code pushes, but genuine project creation. The scorer categorizes repos into engineering (primary), documentation, and configuration, scoring higher for diverse portfolio structures with meaningful READMEs and project documentation.

### 2. Code Consistency (Weight: 11)

Analyzes commit cadence over a rolling 90-day window. Rewards developers with regular, consistent commit patterns rather than burst activity. Detection of healthy contribution rhythms with appropriate weekend/weekday distributions.

### 3. Code Collaboration (Weight: 10)

Counts co-authored Pull Requests and cross-repository collaboration. Captures how well a developer works with teams — multi-author PRs, paired programming sessions, and coordinated feature development all contribute.

### 4. Code Review (Weight: 10)

Evaluates PR review participation: comments left, approvals given, changes requested. Values thoughtful review patterns over drive-by comments. Tracks engagement with both internal and external repositories.

### 5. Issue Discovery (Weight: 9)

Tracks issue creation across repositories, with special weight given to bug reports filed in repos the developer does not own. Rewards proactive problem identification and well-structured issue reporting.

### 6. Issue Resolution (Weight: 9)

Measures issue closure velocity and PR-issue linkage. Rewards developers who close issues with linked pull requests, apply appropriate labels, and drive resolution through completion.

### 7. Context Awareness (Weight: 8)

Evaluates documentation contributions: PR description quality, issue body completeness, wiki edits, and README updates. Rewards developers who communicate clearly and document their work for future contributors.

### 8. Reach and Impact (Weight: 8)

Composite measure of community engagement — stars received, repository forks, and watcher counts. Factors in repository visibility and adoption across the GitHub ecosystem.

### 9. Maintainer Trust (Weight: 7)

Measures explicit repository permissions: collaborator and owner access, team membership, and organization roles. Higher scores for broader responsibility across more repositories.

### 10. Community Engagement (Weight: 7)

Tracks discussion participation across issues, pull requests, and GitHub Discussions. Rewards constructive dialogue, mentorship patterns, and sustained community interaction.

### 11. CI/CD Maturity (Weight: 5)

Analyzes workflow configuration, test coverage indicators, deployment automation, and infrastructure-as-code patterns. Rewards developers who implement robust CI/CD pipelines and maintain clean deployment configurations.

### 12. AI Usage Detection (Weight: 4)

*Brand new — the first behavioral signal of its kind.*

Detects AI-generated commit patterns by analyzing commit message style, diff, and timing distributions. Classifies contributions into AI-only, AI-human hybrid, and purely human patterns. This isn't a penalty — it's transparency. Teams can filter for hybrid native engineers who amplify their output with AI tools while maintaining code quality and comprehension.

---

## Quick Start

## Quick Start

### Via CLI

```bash
# Score any public GitHub profile
gf score torvalds

# Output as JSON
gf score torvalds --json

# Generate a ZK proof of the scoring computation
gf prove torvalds --zk

# Verify an existing attestation
gf verify torvalds

# View a candidate profile
gf profile torvalds

# Start the web server
gf serve
```

### Via Web UI

```bash
pip install -r requirements.txt
export GITHUB_TOKEN="ghp_your_token_here"
# Optional: wallet credentials — wallet creation gracefully degrades when absent
export PRIVY_APP_ID="your_privy_app_id"
export PRIVY_APP_SECRET="your_privy_app_secret"
# Optional: attestation signing key — auto-generated if absent
export ATTEST_PRIVATE_KEY=""
python -m api.main
```

Open http://localhost:8000 -> enter a GitHub username -> get your verifiable skill profile.

> **Wallet note:** Setting `PRIVY_APP_ID` and `PRIVY_APP_SECRET` enables implicit embedded wallet creation on first analysis — no seed phrases, no browser extensions. When these are absent, wallet creation is gracefully disabled and attestation hashes are not stored in a data backpack. See [`.env.example`](.env.example) for all available environment variables. (feat(profile): complete M003 Candidate Profile and update project state)
```

### Via API

```bash
# Get a profile score
curl https://api.githubfingerprint.com/v1/score/torvalds

# Get the full attestation with proof
curl https://api.githubfingerprint.com/v1/attest/torvalds

# Verify attestation offline
curl https://api.githubfingerprint.com/v1/verify/torvalds
```

### Via Web

Visit [githubfingerprint.com/u/torvalds](https://githubfingerprint.com) for a rendered, shareable profile page at `/u/{username}`.

---

## API

```
GET  /v1/score/{username}       → Score + break-down
GET  /v1/attest/{username}      → Score + Ed25519 sig
GET  /v1/verify/{username}      → Verification result
GET  /v1/attest/{username}?zk=1 → Score + Groth16 proof
```

---

## On-Chain Verifier

The deployed contract on Base L2 verifies Groth16 proofs generated by the SP1 zkVM prover. Proof cost: ~$0.008 each. Anyone can verify the exact computation was performed without trusting the server.

Contract address, ABI, and example verification calls are in [/contracts](./contracts).

---

## License

MIT — see [LICENSE](./LICENSE).
