# GitHub Fingerprint — Agent Instructions

## Project Overview

Career-matching platform using GitHub activity as a behavioral fingerprint — code-as-signal replacing resumes and LinkedIn.

## Architecture

- **Python 3.14** | **FastAPI** | **GraphQL API** | **Ed25519 attestations**
- Crawler → Signals → Scoring → API → Attestation

## Key Design Decisions

1. **Path B trust model** — Server-signed attestations now, ZK proofs in Phase 2
2. **Lazy initialization** — `GitHubAPIClient` and `ScoringEngine` are created on first request, not at import
3. **Test isolation** — All GraphQL API calls mocked; no real GitHub token needed for tests

## Workflow Conventions

- **grill-me** first: stress-test design decisions before implementing
- **CE code review**: run multi-agent review after implementation
- **TDD**: vertical tracer bullets, no horizontal slicing
- **Signals are tunable**: magic numbers extracted to named constants in `SignalExtractor`

## Signal Constant Locations

| Signal | Parameter | File | Name |
|--------|-----------|------|------|
| Commit consistency | Confidence denominator | `signals/extractor.py` | `_COMMIT_CONFIDENCE_DENOM` |
| Language diversity | Confidence denominator | `signals/extractor.py` | `_LANGUAGE_CONFIDENCE_DENOM` |
| All confidence thresholds | Per-signal `_*_CONFIDENCE_DENOM` | `signals/extractor.py` | Class-level constants |

## ZK Roadmap

See `docs/zk-research-log.md` for Phase 2 research.
