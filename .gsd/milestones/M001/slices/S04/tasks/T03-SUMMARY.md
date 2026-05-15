---
id: T03
parent: S04
milestone: M001
key_files:
  - index.html
key_decisions:
  - Used GET /score/{username} with ?role= query param instead of POST /score for simpler URL-based score retrieval from the frontend
  - Role dropdown populated from GET /profiles on page load, falling back gracefully if profiles endpoint is unavailable
  - Attestation copy-to-clipboard bundles signature, public_key, signed_payload, and signed_at as JSON for easy sharing and verification
duration: 
verification_result: passed
completed_at: 2026-05-12T06:49:35.598Z
blocker_discovered: false
---

# T03: Upgraded index.html from basic match-only UI to full end-to-end experience with Score/Match tabs, 12-signal breakdown, attestation block, role selector, and fixed API paths

**Upgraded index.html from basic match-only UI to full end-to-end experience with Score/Match tabs, 12-signal breakdown, attestation block, role selector, and fixed API paths**

## What Happened

Upgraded index.html from a minimal match-only page to a complete end-to-end user experience with two modes:

**Score mode**: GitHub username input + role dropdown (populated from GET /profiles on page load via the /profiles endpoint). Displays large overall score, 12-signal breakdown with color-coded score bars (green/amber/red) and confidence percentages, risk flags list, profile name, and full attestation block (truncated signature, truncated public key, signed_at timestamp). Includes copy-to-clipboard for sharing attestation data and a Verify button that POSTs to /verify for real-time cryptographic verification.

**Match mode**: Preserves the original match functionality (username + role description textarea → POST /match) but fixes the API path from /api/match to /match. Shows match score, top reasons list, signal overview, and attestation block with copy/verify.

**Other improvements**: Loading spinner states, error display, toast notifications, Enter key support, responsive layout, and preserved dark monospace aesthetic. Fixed all API paths to remove the /api prefix (the API endpoints are at /score, /match, /profiles, /verify without the prefix).

## Verification

Verification checks pass: index.html contains >20 div elements, references /profiles endpoint, and includes attestation functionality. All 198 tests pass.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -c 'assert open("index.html").read().count("</div>") > 20'` | 0 | ✅ pass | 50ms |
| 2 | `grep -q '/profiles' index.html` | 0 | ✅ pass | 30ms |
| 3 | `grep -q 'attestation' index.html` | 0 | ✅ pass | 30ms |
| 4 | `python -m pytest tests/ -x -v` | 0 | ✅ pass | 970ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `index.html`
