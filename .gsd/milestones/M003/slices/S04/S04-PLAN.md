# S04: ZK Proof Viewer & Badge

**Goal:** Profile page shows a visual proof badge when ZK proof exists for a score. Clicking the badge opens a proof viewer showing proof metadata and verification status.
**Demo:** After this, the profile page shows a visual proof badge when ZK proof exists for a score. Clicking the badge opens a proof viewer showing proof metadata and verification status.

## Must-Haves

- Proof badge in profile shows correct status-specific text and color for all 6 lifecycle states (unknown, pending, proof_generating, proof_generated, on_chain, failed)\n- Expandable proof viewer shows proof metadata: Proof ID, Created, Updated, Tx Hash, Error, Proof Path, and Verifying Contract (when available)\n- Copy Proof Data button works correctly\n- No `/dev/null 2>&1` shell-redirect artifacts in the template\n- Template degrades gracefully (shows "unknown" status) when no proof record exists\n- Template rendering tests cover all proof lifecycle states

## Proof Level

- This slice proves: Integration — slice proves profile page renders ZK proof badge and viewer metadata correctly. Tests mock ProofStatusStore data. No runtime proving infrastructure needed.

## Verification

- The profile page reflects proof status snapshot at render time via `ProofStatusStore`. Missing proof records display "unknown" status gracefully. The `/proof/{username}/status` API endpoint remains the primary inspection surface for detailed proof state.

## Tasks

- [x] **T01: Remove shell-redirect corruption from ZK proof badge spans and copy button** `est:15m`
  Why: `>/dev/null 2>&1` shell-redirect artifacts from a previous bug were injected into 7 locations in the profile.html proof section, breaking Unicode symbol rendering in proof badge spans and the Copy Proof Data button.
  - Files: `templates/profile.html`
  - Verify: grep -c ">/dev/null" templates/profile.html returns 0

- [x] **T02: Surface proof_path and metadata fields in profile viewer for Proof Path and Verifying Contract** `est:30m`
  Why: The profile route constructs `proof_status_data` without `proof_path` or `metadata` from the ProofStatusStore record, so the expandable viewer can't show the proof file path or verifying contract address. R007 requires proof metadata display including verifying contract.
  - Files: `api/main.py`, `templates/profile.html`
  - Verify: pytest tests/test_api.py::TestProofStatusEndpoint -q --tb=short

- [x] **T03: Add profile template rendering tests for all proof lifecycle states** `est:45m`
  Why: No tests verify that the Jinja2 template renders correctly with each proof status state. This is the last untested surface for the proof lifecycle — the API endpoint is tested but the HTML output is not.
  - Files: `tests/test_profile_template.py`, `templates/profile.html`, `api/main.py`
  - Verify: pytest tests/test_profile_template.py -q --tb=short

## Files Likely Touched

- templates/profile.html
- api/main.py
- tests/test_profile_template.py
