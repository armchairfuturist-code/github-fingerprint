# Developer Personality Model — ExO × 4Rs

**Date:** 2026-04-29  
**Status:** Proposal — ready for review and implementation

## Model Overview

Combines the **ExO/SCALE/IDEAS framework** (how someone operates) with the **4Rs segmentation** (their relationship with change and technology) into a unified personality fingerprint.

## The 4Rs Segmentation

| Segment | Prevalence | GitHub Signature |
|---------|-----------|-----------------|
| **Results** | ~5% | Thrives under ambiguity, experiments constantly, prototypes before asked. Multiple languages, diverse projects, quick iteration, contributes to cutting-edge work. |
| **Resilient** | ~15% | Adapts quickly with clear guidance. Structured growth, good docs, follows conventions but not rigid. A bridge between visionaries and the mainstream. |
| **Reluctant** | ~70-75% | Will change with enough evidence. Few languages, mostly cloned repos, original projects limited. Long gaps, minimal community engagement. |
| **Resistant** | ~5-10% | Actively opposed or absent. Minimal or abandoned GitHub presence. May have repositories but private or empty. Hard to detect because they're barely present. |

## Combined ExO × 4Rs Matrix

### SCALE Attributes

| Attribute | Resistant | Reluctant | Resilient | Results |
|-----------|-----------|-----------|-----------|---------|
| **Staff on Demand** | No automation, no CI/CD | Uses templates, basic CI | Builds CI/CD pipelines | Creates automation frameworks, bots |
| **Community & Crowd** | 0 issues, 0 PRs, isolated | Lurks, rarely comments | Participates in issues/PRs | Leads communities, maintains popular repos |
| **Algorithms** | Manual everything | Follows tutorials step-by-step | Builds systematic solutions | Creates frameworks, libraries others use |
| **Leveraged Assets** | Reinvents wheels, no dependencies | Uses popular/obvious libs | Curates dependency choices thoughtfully | Builds on cutting-edge, creates ecosystems |
| **Engagement** | None — zero interaction | Reactive — responds when needed | Responsive — replies within reasonable time | Proactive — seeks out problems to solve |

### IDEAS Attributes

| Attribute | Resistant | Reluctant | Resilient | Results |
|-----------|-----------|-----------|-----------|---------|
| **Interfaces** | No API design, coupled code | Follows framework conventions | Clean, consistent API boundaries | Design-oriented, future-proof abstractions |
| **Dashboards** | No README, no docs | Minimal README (auto-generated) | Well-structured documentation | Comprehensive docs, changelogs, CONTRIBUTING |
| **Experimentation** | Zero — same tools forever | Rarely — tries new tech annually | Sometimes — quarterly experiments | Constant — weekly new tools/methods |
| **Autonomy** | Dependent — only follows | Needs guidance, explicit instructions | Self-directed with clear goals | Creates direction, defines new problems |
| **Social Tech** | Absent — no GitHub interaction | Observer — watches but doesn't act | Participant — engages in discussions | Community builder — creates spaces for collaboration |

## New Signal Mappings

### 1. Ambiguity Comfort Score

Inferred from:
- **Domain diversity** — repos span multiple problem spaces (web, data, infra, CLI, AI)
- **Language switching rate** — new languages adopted over time
- **Project type variety** — libraries, apps, configs, docs, experiments
- **Rigidity index** — inverse of (consistent patterns in commit times, PR sizes, project scopes)

Formula:
```
ambiguity_comfort = domain_diversity * 0.3 + lang_switching_rate * 0.25 
                  + project_variety * 0.25 + (1 - rigidity) * 0.2
```

### 2. Flexibility Score

Inferred from:
- **Iteration velocity** — time between meaningful commits on same project
- **Tool adaptation** — adoption timeline of new languages/frameworks
- **External responsiveness** — how quickly they respond to issues/PRs on their repos
- **Approach switching** — evidence of abandoning one approach for a better one

### 3. Problem-Solving Maturity (Cognitive Signature)

Inferred from:
- **Dependency graph sophistication** — libraries used, their quality, recency
- **Architectural evidence** — commit messages that describe architectural decisions
- **Systematic practices** — tests, CI, linting, type checking
- **Iterative refinement** — commits that improve vs. just add

**This is not "IQ."** It measures learned patterns: systematic thinking, tool fluency, and how someone structures complex work.

### 4. Change Readiness (4Rs Classifier)

Combined scoring heuristic:
```
change_readiness = 
    (community_score * 0.2) +
    (experimentation_score * 0.25) +
    (autonomy_score * 0.2) +
    (engagement_score * 0.15) +
    (learning_velocity * 0.2)

Segment = 
    0-20  → Resistant (or insufficient data)
    21-50 → Reluctant
    51-75 → Resilient
    76-100 → Results
```

## Implementation Priority

| Signal | Complexity | Dependencies | Effort |
|--------|-----------|-------------|--------|
| Ambiguity Comfort | Medium | New extractor | 1 session |
| Flexibility | Low | Existing data + time analysis | 0.5 session |
| Problem-Solving Maturity | High | Commit analysis, dep graph | 2 sessions |
| 4Rs Classifier | Medium | Composited from existing + new | 1 session |
| ExO Matrix Full | High | All of the above | 3 sessions |

## Recommendation

Ship **Flexibility** first (zero new data needed — just better time-series analysis of existing commits). Then **Ambiguity Comfort** (needs domain classification but no new fetches). Save **Problem-Solving Maturity** for Phase 3 (needs README content fetching and dependency analysis).

The **4Rs classifier** can be built incrementally — start with a weighted composite using existing signals, then layer in the new signals as they're built.
