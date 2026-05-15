# M003: Candidate Profile & Sharing

**Depends on:** M002 (ZK Proving Layer)
**Status:** Planned — ready for execution

## Vision

Enable GitHub users to generate and share verifiable skill profiles from their GitHub activity. Each candidate gets a shareable profile page with score breakdowns, Ed25519 attestation, and ZK proof status. Wallet abstraction removes crypto UX barriers. The flow is: analyze → profile → share — no timed tests, no manual portfolio reviews.

## Key Decisions

- UX is thin by design — agents and notifications do the heavy lifting, not app UIs
- Wallet abstraction is critical — if users need Metamask, adoption dies
- Gas fees shouldered by recruiters, not individuals
- Profile link is the shareable unit — unique URL per user
- Profile pages server-rendered for SEO/shareability

## Open Questions (resolved during execution)

- Wallet abstraction provider: Privy recommended (supports Base L2, embedded wallet, no seed phrases). Confirm provider choice in S03.
- Data backpack implementation: ERC-4337 account abstraction on Base, storing attestation hashes. Confirm technical approach in S03.
- ZK proof viewer: Expandable badge component showing metadata, not raw hex. Confirm design in S04.

## Slice Plan

### S01: Shareable Profile Page
Build and serve a shareable, server-rendered candidate profile page with all score data, attestation, and proof status displayed. FastAPI route at /u/{username} renders dark-themed profile with overall score, 12 signal breakdown bars, Ed25519 attestation badge, ZK proof status indicator (pending/generated/on-chain/failed), and GitHub stats summary. Connects to existing /score and /proof/{username}/status endpoints.

### S02: GitHub Opt-In & Crawl Flow
Build the GitHub opt-in flow that triggers the crawl→score→attest pipeline and redirects to the finished profile page. Landing page input for GitHub username, progress polling during crawl, automatic redirect to /u/{username} on completion. Uses existing CrawlCache for incremental freshness.

### S03: Wallet Abstraction & Data Backpack
Integrate a wallet abstraction provider (Privy recommended) for implicit wallet creation on first analysis. No seed phrases, no browser extensions. Implements data backpack storing attestation hashes mapped to wallet addresses.

### S04: ZK Proof Viewer & Badge
Display ZK proof status on the profile page with a visual badge and expandable proof detail viewer. Shows proof metadata: generation timestamp, verifying contract, transaction hash. Copy-proof-data button for power users.

## Technical Assumptions

- Wallet abstraction provider supports Base L2 (verify in S03)
- Profile pages can be server-rendered via Jinja2/HTML templates (no SPA needed)
- Existing /score and /proof/{username}/status endpoints return sufficient data for profile page
- CrawlCache freshness logic handles incrementality without modification
