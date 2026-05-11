# GitHub Fingerprint

Your code is your resume.
Match people to meaningful work through their open-source fingerprint.

---

## The Bet

GitHub repos are becoming a map of how your brain works. Your code reveals:
- Tools you gravitate toward
- How you iterate and debug
- Whether you push through blockers or bail
- How you instruct AI to code
- Your CI/CD maturity
- How you communicate through code

This project scores GitHub users across behavioral signals and produces a cryptographically verifiable fingerprint - not a keyword-stuffed resume.

The thesis: Everyone will need to code to have a white-collar job in the future. GitHub is becoming the default for where code lives, making it the richest signal for what someone can actually do.

## Architecture

GitHub GraphQL -> Deep Crawl Pipeline -> Signal Extractor -> Scoring Engine -> API -> Attestation (Ed25519 + SP1 zkVM) -> Base L2 Verifier

## Trust Model (Phase 1 -> Phase 2)

### Phase 1 (Current) - Server-Signed Attestations (Ed25519)
- Every score response includes a cryptographic attestation
- Server signs with Ed25519 - anyone can verify via /verify
- Key pair auto-generates on first run, stored in .keys/

### Phase 2 (Planned) - ZK Proving via SP1 zkVM
- Scoring function ported to Rust and proven by SP1 (Succinct) zkVM
- Proof verified on Base L2 (~/usr/bin/bash.008/verification)
- Trustless: no server to trust, just math
- Async proving: profile returned immediately with Ed25519; ZK proof upgrades async
- If ZK proving fails, Ed25519 fallback always available

## Signals

| Signal | What It Measures | Proxy For |
|--------|-----------------|-----------|
| commit_consistency | Regularity of commit cadence | Work ethic / persistence |
| language_diversity | Range of programming languages | Adaptability |
| issue_engagement | Issue participation and close rate | Collaborative debugging |
| pr_patterns | PR size balance and merge rate | Code quality |
| project_ownership | Owned vs forked repo ratio | Solo vs collaborative |
| review_patterns | Review comment participation | Technical communication |
| response_time | Time to merge/close | Velocity |
| readme_quality | Repo description quality | Documentation habits |
| (planned) AI usage patterns | Commit timing clusters, message style | AI-augmented development |
| (planned) CI/CD maturity | Workflow configs, automation depth | Engineering discipline |

## Marketplace Model

- Individuals: Always free. Enter your GitHub username, get a deep attested score profile.
- Recruiters: Pay per verification with depth tiers. Higher tiers = deeper analysis + ZK proving.

## Quick Start

pip install -r requirements.txt
export GITHUB_TOKEN="ghp_..."
python -m api.main

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /score | Score a GitHub user (includes attestation) |
| GET | /score/{username} | Score via GET |
| POST | /match | Match user to role description |
| GET | /match/{username}?role=... | Match via GET |
| POST | /verify | Verify a signed attestation |

## Development Roadmap

| Milestone | Description | Status |
|-----------|-------------|--------|
| M001 | Deep pipeline + attested scores | Planning complete |
| M002 | ZK proving layer (SP1 + Base) | Drafted |
| M003 | Candidate profiles + wallet abstraction | Drafted |
| M004 | Recruiter dashboard + marketplace | Drafted |
| M005 | Matchmaking + notifications | Drafted |

## Test Suite

python -m pytest tests/ -v

## Architecture Decisions

See .gsd/DECISIONS.md for the full register of architectural decisions and rationale.
