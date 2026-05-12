# Cycle Count Feasibility Report — Rust Scoring Lib for SP1

**Date:** 2026-05-12  
**Target:** M002 S01 (Rust Scoring Library)  
**Status:** ✅ Feasible — estimated < 200K RISC-V cycles for typical input

## Methodology

Since the SP1 toolchain (`cargo prove`) could not be installed in the current Windows/MSYS2 development environment (see failure-mode rationale below), cycle counts are estimated via:

1. **Operation counting** — counting loops, sorts, string operations, and hash-map operations in each signal function
2. **RISC-V instruction mapping** — mapping Rust constructs to RISC-V instruction equivalents
3. **Upper-bound estimation** — using worst-case input sizes (50 commits, 30 repos, 20 PRs, 20 issues)

## Per-Signal Cycle Estimates

| Signal | Operations | Estimated Cycles | Bound |
|---|---|---|---|
| commit_consistency | Sort commits, diff calculation, std dev | 5,000-15,000 | 20K |
| language_diversity | Count languages, entropy calc | 2,000-5,000 | 10K |
| issue_engagement | Sum counters, rate calculations | 1,000-3,000 | 5K |
| pr_patterns | Sum counters, merge rate, balance ratio | 1,000-3,000 | 5K |
| project_ownership | Categorize owned vs forked | 500-2,000 | 3K |
| review_patterns | Sum comment counters | 500-1,000 | 2K |
| response_time | Parse dates, compute diff | 3,000-10,000 | 15K |
| readme_quality | Content analysis, struct counting | 5,000-20,000 | 30K |
| commit_semantics | String matching, regex-like prefix checks | 10,000-30,000 | 50K |
| cicd_maturity | HashMap queries and frequency analysis | 2,000-5,000 | 10K |
| contribution_consistency | Parse days, gap/streak analysis | 10,000-50,000 | 80K |
| ai_usage_patterns | Length variance, burst detection, string analysis | 5,000-20,000 | 30K |
| **Score combination** | Weighted sum, threshold filtering, risk flags | 1,000-3,000 | 5K |
| **Serde I/O** | JSON parse + serialize | 10,000-30,000 | 50K |
| **Total** | | **~56K-197K** | **~315K** |

## Headroom Analysis

- **Soft limit (SP1 "fast" mode):** ~50M cycles (CPU proving in ~30s)
- **Hard limit (SP1 default):** ~100M cycles (prover network, ~2 min)
- **Our estimate:** ~200K cycles — **250x headroom** vs soft limit

Even with 10x underestimation, we're at **2M cycles** with 25x headroom to the soft limit.

## Optimization Candidates (if needed)

These signals could be optimized further, though unlikely necessary:

1. **contribution_consistency** — Currently iterates all contribution days (365/year). Can be sampled.
2. **commit_semantics** — String matching for conventional commits. Could use simpler prefix check.
3. **readme_quality** — Full content analysis loops. Can truncate content to first 2KB.

## SP1-Specific Considerations

### Memory
- RISC-V guest has 256MB memory by default
- Our data structures: ScoreInput with 50 commits ~ 100KB serialized
- Heap allocations via `alloc`/`std` are fine within budget

### Dependencies
- `serde` + `serde_json` — well-tested in SP1 (commonly used)
- `chrono` — date parsing and arithmetic. Critical path: used in response_time, contribution_consistency, ai_usage_patterns. If `chrono` is problematic in no_std, replace with manual timestamp parsing (ISO 8601 → seconds since epoch)

### no_std Compatibility
- SP1 guest programs use `#![no_std]` + `extern crate alloc`
- Our types crate (`scoring-types`) uses `std::collections::BTreeMap` — needs to switch to `alloc::collections::BTreeMap`
- `serde_json` in no_std mode uses the `alloc` feature flag
- `chrono` has a `no-std` feature but it's limited — may need a custom thin date parser for the SP1 guest

## SP1 Toolchain Installation Failure

On the current Windows/MSYS2 development environment:
- `sp1up` downloaded `cargo_prove_v6.1.0_win32_amd64.zip` successfully
- MSYS2's `unzip` could not extract it (Windows zip format incompatibility)
- Resolution: install SP1 on a Linux/macOS machine, or use WSL2 on Windows

Once installed, verify cycle counts with:
```bash
cargo prove build
cargo prove measure --input <scoring_input.json>
```

## Verdict

| Criterion | Result |
|---|---|
| Cycle count feasibility | ✅ < 200K estimated, 250x headroom |
| no_std compatibility | ⚠️ Minor changes needed (alloc::collections, serde_json alloc feature) |
| RISC-V compilation | ✅ No platform-specific code (no syscalls, no filesystem, no networking) |
| SP1 toolchain available | ❌ Not on this Windows host (manual install needed) |

**Recommendation:** Proceed to S02 (SP1 Prover Pipeline) after installing SP1 toolchain on a Linux/macOS machine or WSL2. The cycle headroom is sufficient — the Rust scoring lib is well within SP1's proving budget.
