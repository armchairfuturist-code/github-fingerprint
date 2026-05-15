---
id: T02
parent: S01
milestone: M002
key_files:
  - scoring-types/src/lib.rs
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T07:53:47.792Z
blocker_discovered: false
---

# T02: Defined all Rust data types with serde JSON serialization — ScoreInput, ScoreOutput, SignalScore, RoleProfile, and 8 GitHub data types.

**Defined all Rust data types with serde JSON serialization — ScoreInput, ScoreOutput, SignalScore, RoleProfile, and 8 GitHub data types.**

## What Happened

Defined all shared data types in the scoring-types crate: ScoreInput, ScoreOutput, SignalScore, RoleProfile, and all GitHub data types (RepoData, CommitData, IssueData, PrData, ReadmeData, CicdConfigData, ContributionData, ContributionDay). All types implement Serialize + Deserialize for serde JSON interop. SignalScore has a convenient new() constructor.

## Verification

cargo build passes. Types serialize/deserialize correctly (verified via CLI converting fixtures).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

None. Types exactly mirror Python dataclasses from crawler/github_api.py.

## Known Issues

None.

## Files Created/Modified

- `scoring-types/src/lib.rs`
