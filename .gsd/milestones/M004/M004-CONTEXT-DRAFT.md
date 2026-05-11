---
depends_on: [M003]
---

# M004: Recruiter Dashboard & Marketplace (DRAFT)

**Status:** Draft — refine before executing

## Seed Material

### Architecture
- **Dashboard:** Web UI for recruiters — search candidates, filter by signals/role/budget
- **Billing:** Pay-per-verification with depth tiers. Gas costs baked into tier pricing.
- **API:** Recruiter-facing API for programmatic candidate searching and proof verification
- **Auth:** Recruiter accounts with API keys

### Key Decisions (from M001 discussion)
- Recruiters pay for verification depth — deeper analysis = higher tier = higher cost
- Individuals always free — this drives adoption
- Candidates who opted in are discoverable via search
- "Survey/guide" that helps recruiters refine candidates vs budget and scope needs

### Provisional Slices
- S01: Recruiter Search & Filter — Search candidates by signals, role type, verification tier. Budget/scope-guided refinement flow.
- S02: Pay-per-Verification — Tiered pricing integration. Payment processing. Gas cost tracking and billing.

### Open Questions
- Pricing tiers — what's the structure? Per-verification? Subscription? Credits?
- How does the "refinement survey/guide" work UX-wise?
- Do recruiters need an API or just the dashboard?
- What payment processor? Stripe? Crypto-native?
- KYC/onboarding for recruiters — required?
