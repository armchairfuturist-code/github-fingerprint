---
id: T01
parent: S04
milestone: M003
key_files:
  - templates/profile.html
key_decisions: []
duration: 
verification_result: passed
completed_at: 2026-05-15T05:43:14.965Z
blocker_discovered: false
---

# T01: Removed 7 shell-redirect artifacts (">/dev/null 2>&1") from the profile proof badge and copy button

**Removed 7 shell-redirect artifacts (">/dev/null 2>&1") from the profile proof badge and copy button**

## What Happened

All 7 occurrences of `>/dev/null 2>&1` were injected before Unicode symbols in the proof badge spans (lines 175-180) and the Copy Proof Data button (line 235). Removed them all in two surgical edits — one for the badge section, one for the copy button. Also fixed the proof_generating line which had a double corruption: `>/dev/null 2>&1 &#9678; Generating>/dev/null 2>&1 &#8230;` → `&#9678; Generating &#8230;`.

## Verification

grep -c ">/dev/null" templates/profile.html returns 0 (exit code 1, no matches). 372 tests pass.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -c ">/dev/null" templates/profile.html` | 1 | ✅ pass — 0 occurrences found | 50ms |
| 2 | `pytest -q --tb=short` | 0 | ✅ pass — 372 tests pass | 1920ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `templates/profile.html`
