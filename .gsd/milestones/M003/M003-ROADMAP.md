# M003: Candidate Profile & Sharing

**Vision:** Enable GitHub users to generate and share verifiable skill profiles from their GitHub activity. Each candidate gets a shareable profile page with score breakdowns, Ed25519 attestation, and ZK proof status. Wallet abstraction removes crypto UX barriers. The flow is: analyze → profile → share — no timed tests, no manual portfolio reviews.

## Success Criteria

- Shareable profile page at /u/{username} renders all score signals with descriptive labels and breakdown bars
- Profile includes Ed25519 attestation badge showing verified/not-verified status
- Profile shows ZK proof status indicator (pending/generated/on-chain)
- GitHub opt-in flow: enter username → crawl → score → redirect to profile
- Opt-in shows crawl progress to the user during processing
- Wallet abstracted — no seed phrases, no MetaMask, no browser extensions
- Data backpack stores attestation hashes per user
- Proof badge with expandable viewer shows proof metadata (timestamp, verifying contract)

## Slices

- [x] **S01: S01** `risk:medium` `depends:[]`
  > After this: After this, a user visiting /u/{username} sees a polished dark-themed profile page with overall score, signal breakdown bars, Ed25519 attestation badge, proof status indicator (pending/generated/on-chain), and GitHub stats summary.

- [x] **S02: S02** `risk:medium` `depends:[]`
  > After this: After this, a user can enter their GitHub username, trigger a fresh crawl + score, and immediately see their profile page with updated results. Crawl status is tracked and shown during processing.

- [x] **S03: S03** `risk:high` `depends:[]`
  > After this: After this, first-time users get an implicit wallet created (no seed phrases, no browser extensions). The wallet stores attestation hashes — a 'data backpack' of verified credentials.

- [x] **S04: S04** `risk:high` `depends:[]`
  > After this: After this, the profile page shows a visual proof badge when ZK proof exists for a score. Clicking the badge opens a proof viewer showing proof metadata and verification status.

## Boundary Map

Not provided.
