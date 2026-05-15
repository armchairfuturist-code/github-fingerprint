---
id: S04
parent: M003
milestone: M003
provides:
  - Clean, tested profile page with ZK proof badge and expandable metadata viewer. Downstream consumers can verify proof status per lifecycle state through rendered HTML, not just the JSON API endpoint.
requires:
  []
affects:
  []
key_files:
  - templates/profile.html
  - api/main.py
  - tests/test_profile_template.py
key_decisions:
  - When patching get_store in tests, must use api.main.get_store not api.proof_status.get_store — the from-import creates a separate binding
  - proof_path and verifying_contract surfaced as conditional template rows (Jinja2 if blocks), matching existing pattern for tx_hash and error
patterns_established:
  - (none)
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-05-15T05:43:57.399Z
blocker_discovered: false
---

# S04: ZK Proof Viewer & Badge

**Fixed template corruption, added proof_path and verifying_contract fields to profile viewer, and added 23 template rendering tests covering all proof lifecycle states**

## What Happened

S04 completed the ZK Proof Viewer & Badge with three focused tasks. T01 removed 7 instances of `>/dev/null 2>&1` shell-redirect corruption from the profile template that were breaking Unicode symbol rendering in proof badge spans and the Copy Proof Data button. T02 surfaced two missing metadata fields — proof_path (from the ProofStatusStore top-level field) and verifying_contract (from the metadata sub-dict) — in both the profile route and the expandable proof viewer template, future-proofed for when the proving pipeline stores the contract address. T03 added 23 comprehensive Jinja2 template rendering tests across 4 test classes covering all 6 proof lifecycle states (badge text and symbols), viewer metadata display, graceful degradation when no proof record exists, and copy button verification.

## Verification

All tasks verified independently. T01: grep confirms zero shell-redirect artifacts. T02: 8 proof status endpoint tests + 8 profile tests pass. T03: 23 new template tests pass. Full suite: 372 tests pass.

## Requirements Advanced

- R007 — ZK proof badge and viewer now correct (T01 fix) and more complete (T02 proof_path + verifying_contract)

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

None.
