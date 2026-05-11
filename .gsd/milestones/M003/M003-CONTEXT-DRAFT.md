---
depends_on: [M002]
---

# M003: Candidate Profile & Sharing (DRAFT)

**Status:** Draft — refine before executing

## Seed Material

### Architecture
- **Frontend:** Thin web UI — candidate profile pages, ZK proof viewer, Ed25519 attestation display
- **Backend:** FastAPI serves profile data from PostgreSQL. Profile endpoint returns scores, signals, attestation, proof status.
- **Wallet:** Abstracted wallet creation (Web3Auth/Privy-like pattern). Users never manage keys. "Data backpack" concept.
- **GitHub opt-in:** Simple flow — "analyze my profile" button that kicks off the crawl pipeline

### Key Decisions (from M001 discussion)
- UX is thin by design — agents and notifications do the heavy lifting, not app UIs
- Wallet abstraction is critical — if users need Metamask, adoption dies
- Gas fees shouldered by recruiters, not individuals
- Profile link is the shareable unit — unique URL per user

### Provisional Slices
- S01: Candidate Profile Page — Shareable URL with score, signal breakdown, Ed25519 attestation badge, ZK proof status indicator. Dark-themed, minimal.
- S02: Wallet Abstraction — Integration with wallet abstraction provider. Implicit wallet creation on first analysis. "Data backpack" concept — the wallet stores the user's attestation history.

### Open Questions
- Which wallet abstraction provider? Privy, Web3Auth, Dynamic — research needed.
- How does the "data backpack" concept work technically? ERC-4337 account abstraction on Base?
- What does the ZK proof viewer look like? Raw hex dump or rendered badge?
- How does recruiter-initiated contact work from the profile page?

### Technical Assumptions (VERIFY before CONTEXT.md)
- Chosen wallet abstraction provider supports Base L2
- Profile pages can be server-rendered (SSR) for SEO/shareability
