# M001: Deep Pipeline & Attested Scores

**Vision:** Build the deep GitHub mining pipeline and role-adaptive scoring engine. Expand the existing MVP crawler from 8 shallow signals to deep multifactor analysis — README content, commit semantics, contribution graphs, CI/CD indicators, AI usage patterns. Restructure scoring for role-adaptive weights. Extend Ed25519 attestation to cover all new signals. Ship a standalone useful product: enter username, get a deep attested score profile.

## Slices

- [x] **S01: S01** `risk:high` `depends:[]`
  > After this: Crawler fetches README content, detects CI/CD configs, analyzes commit patterns, and caches results for incremental updates.

- [x] **S02: S02** `risk:high` `depends:[]`
  > After this: Scoring engine supports multiple role profiles with different signal weights.

- [x] **S03: S03** `risk:low` `depends:[]`
  > After this: Every score carries an independently verifiable Ed25519 signature covering all signals.

- [x] **S04: S04** `risk:low` `depends:[]`
  > After this: Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates.

## Boundary Map

Not provided.
