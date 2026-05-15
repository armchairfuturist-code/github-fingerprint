# Sprint 001 — Shareable Fingerprint & Deploy

**Date:** 2026-04-29  
**Source:** CEO Plan Review (hold scope + outside voice)  
**Status:** Planned

## Summary

Deploy a shareable `/fingerprint/{username}` HTML page. Fix the 32-call GraphQL bottleneck. Show the fingerprint to one hiring manager.

## Artifacts from This Session

| Artifact | Location |
|----------|----------|
| Personality model spec | `docs/personality-model.md` |
| ZK research agenda | `docs/zk-research-log.md` |
| CEO review output | `docs/plans/sprint-001.md` (this file) |
| Grill-me decisions | In memory + git log |
| CE code review fixes | git log (P0/P1 fixes) |

## Sprint Goals

1. **Deploy** — `/fingerprint/{username}` HTML endpoint on Railway/Render ($5/mo)
2. **Optimize** — Batch GraphQL queries (32 calls → ~11 calls per fingerprint)
3. **Validate** — Show fingerprint to one hiring manager. Record reaction. Do not build more until this happens.

## Tasks

### Task 1: Batch GraphQL Queries (P0)
- Current: 1 (user) + 1 (repos) + 10×3 (commits+issues+prs per repo) = 32 calls
- Target: Combine commits/issues/PRs into a single query per repo → 1 + 1 + 10 = 12 calls
- Also combine user + initial repo list into one query

### Task 2: Fingerprint HTML Page
- New route: `GET /fingerprint/{username}` returns styled HTML
- Design: Dark theme, monospace personality matrix, ExO badges, attestation seal
- Inspired by: Stripe's user profiles / GitHub's own profile page
- Self-contained: inline CSS, no JS dependencies
- Response headers: include `X-Attestation-Signature` for programmatic verification

### Task 3: Deploy
- Target: Railway.app (Python worker, $5/mo plan)
- Configuration: `requirements.txt`, `Procfile`, `GITHUB_TOKEN` env var
- Custom domain or `railway.app` subdomain
- Post-deploy: smoke test with `armchairfuturist-code`

## Blockers

| Blocker | Status | Resolution |
|---------|--------|------------|
| GitHub token rate limit | Open | Batch queries first. Then evaluate dedicated token or bring-your-own |
| Personality model validation | Open | Defer to first human review of fingerprint output |
| Deploy platform choice | Open | Evaluate Railway vs Render vs fly.io |

## CEO Review Action Items

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Deploy shareable fingerprint page | Build | Planned |
| 2 | Fix 32-call GraphQL bottleneck | Build | Planned |
| 3 | Show fingerprint to one hiring manager | You | External |

## Next Sprint (Sprint 002 — GitHub App)

After validation from Sprint 001, the next iteration is the GitHub App:
- PR lifecycle monitoring (time-to-review, bottleneck detection, iteration cycles)
- Team health dashboard
- Free for OSS, paid for private repos
- Revenue + signal data + enterprise entry point

## Product Roadmap

```
Sprint 001 ─── Fingerprint page + deploy + validation
     │
     ▼
Sprint 002 ─── GitHub App (team telemetry, B2B wedge)
     │
     ▼
Sprint 003 ─── Personality model v2 (trained on real data from bot)
     │
     ▼
Phase 2   ─── ZK proofs (Noir) + on-chain attestations (EAS)
```

## Key Decisions

1. **ZK is not optional** — it's the trust layer that makes this a marketplace, not a harvester. But it's Phase 2. Phase 1 proves demand.
2. **Personality model is speculative** — shipped as hypothesis, improves with opt-in data. ZK makes opt-in riskless.
3. **Distribution is the gap** — the fingerprint page is lead gen. The GitHub App is the revenue engine. Both feed the same personality model.
