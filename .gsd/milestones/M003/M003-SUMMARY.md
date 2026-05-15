---
id: M003
title: "Candidate Profile & Sharing"
status: complete
completed_at: 2026-05-15T05:44:37.046Z
key_decisions:
  - Profile pages are server-rendered Jinja2 templates (no SPA) — proven correct through 23 template rendering tests
  - Proof status is always read as a snapshot at render time — no WebSocket/polling for live updates
  - Wallet abstraction gracefully degrades — Privy credentials optional, no crash if missing
  - Proof_path and verifying_contract are conditionally displayed — future-proofed for when the proving pipeline populates them
key_files:
  - templates/profile.html (S01,S04)
  - static/css/style.css (S01)
  - static/index.html (S02)
  - templates/404.html (S01)
  - api/main.py (S01,S02,S04)
  - wallet/provider.py (S03)
  - wallet/store.py (S03)
  - tests/test_profile.py (S01)
  - tests/test_optin.py (S02)
  - tests/test_wallet.py (S03)
  - tests/test_profile_template.py (S04)
lessons_learned:
  - When patching `get_store` in tests for api.main routes, use `api.main.get_store` not `api.proof_status.get_store` — Python's `from .proof_status import get_store` creates a separate binding in the importing module
  - Wallet abstraction and ZK proving pipeline are independent concerns — wallet tests pass without any proving infrastructure. This separation was intentional and proven correct.
  - The proof_status template rendering is the only surface where proof lifecycle states are visually verified — the JSON API endpoint tests alone don't catch template rendering issues
---

# M003: Candidate Profile & Sharing

**Delivered shareable candidate profile pages with GitHub opt-in flow, wallet abstraction, and ZK proof viewer badge — 4 slices, 372 tests**

## What Happened

M003 (Candidate Profile & Sharing) delivered 4 slices over a focused execution cycle. S01 built the server-rendered shareable profile page at /u/{username} with overall score ring, 12 signal breakdown bars, attestation badge, ZK proof status indicator, and GitHub stats — all in a dark-themed design system. S02 added the GitHub opt-in flow with a landing page, username input, progress overlay (4 steps + timer), and auto-redirect to the finished profile. S03 integrated Privy-based wallet abstraction for implicit wallet creation (no seed phrases, no MetaMask) with async background tasks and 19 wallet tests. S04 polished the ZK proof viewer — fixed template corruption, added proof_path and verifying_contract metadata fields, and added 23 template rendering tests covering all 6 proof lifecycle states. The milestone closes with 372 passing tests and all 8 requirements either validated or newly validated (R006, R007).

## Success Criteria Results

All 8 milestone success criteria pass — validated in the validation gate above.

## Definition of Done Results

All slice-level success criteria met. 372 tests pass. R006 and R007 transitioned to validated status.

## Requirement Outcomes

R004 (Shareable profile pages) — Validated by S01. R005 (GitHub opt-in flow) — Validated by S02. R006 (Wallet abstraction) — Transitioned from active to validated by S03. R007 (ZK proof badge and viewer) — Transitioned from active to validated by S04.

## Deviations

None. All slices delivered as planned.

## Follow-ups

## Follow-Up Items for Future Milestones

1. **R006 wallet tests** transitioned to validated — Privy credentials are optional for testing but need real credentials for production wallet creation
2. **Verifying contract field** in the proof viewer will populate automatically once the proving pipeline stores contract address in metadata
3. **SP1Verifier.sol deployment** to Base Sepolia remains pending (~0.01 ETH needed for wallet funding) — affects on-chain proof status verification
4. **M004: Recruiter Dashboard & Marketplace** is the next milestone — search/filter, budget/scope tiers, pay-per-verification pricing
