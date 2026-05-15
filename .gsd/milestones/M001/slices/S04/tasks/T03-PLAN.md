---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Upgrade frontend to full end-to-end user experience

Upgrade index.html from a basic match-only UI to a complete end-to-end experience. Fix the API path (remove /api prefix). Add: (1) Tab/mode selector: Score vs Match. (2) Score mode with GitHub username input and role dropdown (populated from GET /profiles on page load). (3) Score result display: large overall score, 12-signal breakdown with score bars, risk flag list, profile name. (4) Attestation block display: signature (truncated), public_key (truncated), signed_at timestamp, copy-to-clipboard for sharing. (5) Match mode keeps existing functionality but fixes API paths. (6) Loading states, error handling, responsive layout. (7) Preserve existing dark monospace aesthetic.

## Inputs

- `index.html`

## Expected Output

- `index.html`

## Verification

python -c 'assert open("index.html").read().count("</div>") > 20' && grep -q '/profiles' index.html && grep -q 'attestation' index.html
