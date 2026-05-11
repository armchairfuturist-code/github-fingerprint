# M001: Deep Pipeline & Attested Scores

**Gathered:** 2026-05-11
**Status:** Ready for planning

## Project Description

Build the deep GitHub mining pipeline and role-adaptive scoring engine. Expand the existing MVP crawler from 8 shallow signals to a deep multifactor analysis — README content, commit message semantics, contribution graphs, CI/CD indicators, AI usage patterns. Restructure the scoring engine for role-adaptive weights. Extend the existing Ed25519 attestation to cover all new signals. Ship a standalone useful product: a user enters their GitHub username and gets a deep, attested score profile they can share.

## Why This Milestone

The current MVP has a solid foundation (crawl, 8 signals, scoring, attestation) but the signals are shallow and role-agnostic. Before we can add ZK proving (M002), we need a scoring pipeline worth proving. This milestone makes the product immediately useful — a candidate gets a genuinely insightful fingerprint that a recruiter can verify independently — without waiting for the ZK layer.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Enter their GitHub username and get a deep multifactor analysis of their code
- See a role-adaptive score and signal breakdown (different weights for engineering vs marketing vs non-technical roles)
- Get an Ed25519-signed attestation that anyone can verify independently via `/verify`
- Return later and get incremental updates (no re-crawl from scratch)
- Share a link to their attested profile

### Entry point / environment

- Entry point: Web UI (existing `index.html` upgraded) + `/score/{username}` API
- Environment: Local dev / deployed API server
- Live dependencies involved: GitHub GraphQL API, local Ed25519 key pair

## Completion Class

- Contract complete means: All new signal extractors have unit tests. Scoring engine handles role-adaptive weights. Attestation covers all new signals.
- Integration complete means: Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning user gets incremental update.
- Operational complete means: API serves requests under 30s total (crawl dominates). Rate limit handling works. Tests pass.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A real GitHub user can be scored end-to-end with the new deep pipeline (test against a known account)
- The resulting attestation can be verified by a third party using only the `/verify` endpoint
- A returning user's second crawl is measurably faster (~80% fewer API calls) due to caching

## Architectural Decisions

### SP1 zkVM for Scoring Prover

**Decision:** SP1 (Succinct) zkVM for proving scoring function execution. Scoring function ported to Rust. Proving happens async; Ed25519 attestation is the instant fallback.

**Rationale:** SP1 leads in production adoption (6M+ proofs, $3B+ TVL), lowest proving cost ($0.02–$0.10/proof), fastest latency (~2 min), and formal verification passed. The zkVM model proves arbitrary Rust execution without circuit constraints — far more evolvable than a circuit DSL.

**Alternatives Considered:**
- RISC Zero zkVM — Open-source, slightly higher cost ($0.04–$0.17/proof), slower proving. Viable alternative if open-source requirement becomes critical.
- Noir (Aztec) — Circuit DSL, not a general-purpose zkVM. Would require writing the scoring function as explicit circuit constraints — not evolvable.
- Ed25519-only (no ZK) — Already works and stays as fallback, but doesn't provide trustless verification.

### Base L2 for On-Chain Proof Verification

**Decision:** Deploy SP1 verifier contract on Base L2. Verification cost ~$0.008/proof.

**Rationale:** Base has the lowest verification cost among major L2s, EVM-compatible, integrates with SP1 via OP Succinct (SP1 is default proving system for OP Stack).

**Alternatives Considered:**
- Arbitrum — Official Succinct partnership but ~5x higher verification cost ($0.04).
- Ethereum L1 — ~$1.35 verification cost — too expensive per-proof.

### Async Proving with Ed25519 Fallback

**Decision:** Profile returned immediately with Ed25519 attestation. ZK proof upgrades async. ZK failure never blocks the user.

**Rationale:** 1-5 min proving latency must not block UX. Ed25519 is the instant safety net. ZK is a trust upgrade, not a gate.

### Scoring Algorithm is a Living System

**Decision:** Signal weights and analysis depth are role-adaptive and iterate based on real usage. Not a build-once spec.

**Rationale:** The signal mix for a marketing role is fundamentally different from engineering. Iteration based on usage data is the only way to get this right.

### Marketplace Model: Free Individuals, Paid Recruiters

**Decision:** Individuals always free. Recruiters pay per verification with depth tiers. Gas costs included.

**Rationale:** Free drives adoption and data network effects. Recruiter revenue sustains proving/verification costs.

## Error Handling Strategy

All failures follow the async fallback pattern: the user always gets a response, never a timeout or hang. Structured JSON errors throughout.

### Crawl failures
- Partial crawl (rate limit): Score on available data with transparency. Profile says "Analyzed 12/15 repos."
- Token exhausted: Queue the request, return 202. Profile status: "Analysis queued."
- User has no public repos: Return "No public GitHub activity found." Zero score vs null data is a meaningful distinction.
- Returning user: Cache by (username, date). Only re-fetch repos pushed since last crawl.

### Scoring failures
- Signal computation errors are isolated per signal. One signal failure does not crash the whole score.
- Scores clamp to 0-100. Edge cases (single commit, zero repos) produce bounded outputs, not NaN.

### Attestation failures
- Key pair generation failure on startup: Server refuses to start. Ed25519 keys are critical infrastructure.
- Signing failure mid-operation: Returns HTTP 500. Attestation infrastructure must be healthy.

> See `.gsd/DECISIONS.md` for the full append-only register of all project decisions.

## Risks and Unknowns

- **Signal quality for solo developers** — The existing signals lean toward collaborative patterns (PRs, reviews, issues). Solo devs may score poorly or have low-confidence signals. Research needed during M001 to find what signals work for non-collaborative profiles.
- **Role-adaptive weights accuracy** — Initial weights will be guesses validated against real usage. We need a feedback loop to learn what signals actually correlate with hiring outcomes.
- **AI usage detection feasibility** — Detecting AI-assisted vs human-written commits from metadata alone may be unreliable. May need content-level analysis (diff patterns, message structure, timing clusters).
- **Crawl latency** — Deep mining (README content, contribution graphs, all commits) multiplies crawl time. 30s target may require parallel crawling or streaming results.

## Existing Codebase / Prior Art

- `crawler/github_api.py` — GraphQL client with rate limiting, data classes for user/repo/commit/issue/PR, `get_user_activity()` fetches everything for a user
- `signals/extractor.py` — 8 signal extractors (commit_consistency, language_diversity, issue_engagement, pr_patterns, project_ownership, review_patterns, response_time, readme_quality)
- `scoring/engine.py` — Weighted scoring engine with configurable weights, risk flag generation, ScoreResult dataclass
- `api/main.py` — FastAPI with /health, /score, /match, /verify endpoints
- `index.html` — Dark-themed monospace web UI
- `tests/test_crawler.py` — Mock-based tests for GraphQL client
- `tests/test_scoring.py` — Tests for scoring engine with mock signal results

## Relevant Requirements

- R001 — Deep GitHub Mining: Owned by S01 (expand crawler) and S02 (feed into scoring)
- R002 — Role-Adaptive Scoring: Owned by S02 (restructure scoring engine)
- R003 — Ed25519 Attestation: Owned by S03 (extend to new signals)
- R012-R017 — Validated: Already exist from current codebase

## Scope

### In Scope

- Expand GitHub crawler: README content, contribution graph analysis, commit message semantics, CI/CD detection, AI usage pattern detection
- Incremental freshness caching: cache by (username, date), only re-fetch repos pushed since last crawl
- Role-adaptive scoring: multiple role profiles with different signal weights
- Signal improvements: refactor existing 8 signals for depth, add new signals
- Ed25519 attestation extension: cover all new signals in the signed payload
- /verify endpoint improvements
- Test coverage for all new components
- Performance: crawl time under 30s, cache hit ~80% for returning users

### Out of Scope / Non-Goals

- ZK proving (M002)
- Candidate profile pages (M003)
- Wallet abstraction (M003)
- Recruiter dashboard (M004)
- Pay-per-verification pricing (M004)
- Any on-chain infrastructure (M002)

## Technical Constraints

- Must not break existing /score and /match API contracts
- Must maintain backward compatibility with existing signal data format
- Ed25519 key pair persists across restarts (already stored in `.keys/`)
- GITHUB_TOKEN env var required (already documented)
- All new code must have test coverage

## Integration Points

- GitHub GraphQL API — primary data source. Rate limit: 5,000 pts/hr. Must handle partial crawl gracefully.
- Existing FastAPI — all new endpoints and signal data must integrate without breaking existing routes
- Ed25519 key store — `.keys/` directory on disk. Key pair auto-generates on first run.

## Testing Requirements

- Unit tests for all new signal extractors (mock GitHub data)
- Unit tests for role-adaptive scoring engine (multiple role profiles)
- Unit tests for crawl caching and incremental freshness logic
- Integration test: end-to-end crawl → score → attest against a test GitHub account (optional, requires token)
- Existing tests must continue to pass

## Acceptance Criteria

### S01 — Deep GitHub Pipeline
- Crawler fetches README content for each repo
- Crawler detects CI/CD configuration files (.github/workflows, Jenkinsfile, etc.)
- Crawler analyzes contribution graph (commit density over time, gaps)
- Crawler extracts commit message patterns (length, structure, conventional commits)
- Crawler detects AI usage patterns (commit timing clusters, message style shifts)
- Incremental cache: second crawl of same user fetches <20% of original API calls
- Crawl completes under 30s for users with <50 repos

### S02 — Role-Adaptive Scoring
- At least 3 role profiles exist (engineering, marketing, non-technical) with distinct weights
- Scoring engine accepts a role parameter and applies appropriate weights
- Each signal has a minimum confidence threshold; below threshold, signal is flagged not scored
- All existing 8 signals continue to work

### S03 — Attestation Upgrade
- Ed25519 attestation payload includes all new signal scores
- /verify endpoint validates a signature against the server's public key
- Attestation format documented for third-party verification

### S04 — Integration
- Full end-to-end flow works: enter username → crawl → score → attest
- Returning user flow: cached data served, only new activity fetched
- Test suite passes
- API documentation updated

## Open Questions

- What concrete signals best capture solo developer quality? Investigate during S01.
- How do we validate role-adaptive weights against real hiring outcomes? This is a long feedback loop.
- AI usage detection: can we detect it reliably from commit metadata alone, or do we need diff content analysis? Research during S01.
