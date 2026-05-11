# M001: Deep Pipeline & Attested Scores

**Vision:** Build the deep GitHub mining pipeline and role-adaptive scoring engine. Expand the existing MVP crawler from 8 shallow signals to deep multifactor analysis — README content, commit semantics, contribution graphs, CI/CD indicators, AI usage patterns. Restructure scoring for role-adaptive weights. Extend Ed25519 attestation to cover all new signals. Ship a standalone useful product: enter username, get a deep attested score profile.

## Slices

- [ ] **S01: Deep GitHub Pipeline** `risk:high` `depends:[]`
  > After this: Crawler fetches README content, detects CI/CD configs, analyzes commit patterns, and caches results for incremental updates.

- [ ] **S02: Role-Adaptive Scoring** `risk:high` `depends:[S01]`
  > After this: Scoring engine supports multiple role profiles with different signal weights.

- [ ] **S03: Attestation Upgrade** `risk:low` `depends:[S02]`
  > After this: Every score carries an independently verifiable Ed25519 signature covering all signals.

- [ ] **S04: Integration & Polish** `risk:low` `depends:[S01,S03]`
  > After this: Full end-to-end flow: enter username → deep crawl → score → attest → share. Returning users get incremental updates.

## Boundary Map

Not provided.
