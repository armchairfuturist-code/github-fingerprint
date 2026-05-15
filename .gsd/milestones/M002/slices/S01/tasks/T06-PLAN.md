---
estimated_steps: 6
estimated_files: 1
skills_used: []
---

# T06: Cycle count profiling for SP1 feasibility

Add a cycle count estimation step:
- Build a minimal SP1 program stub (no prover) that calls the Rust scoring lib
- Use SP1's `sp1-helper` or manual approach to get RISC-V cycle count
- Report cycle count in an analysis doc
- If cycles > 10M, identify heaviest signals for optimization

Output: cycle-count-report.md with measured or estimated cycle counts per signal and total.

## Inputs

- `scoring-core/src/lib.rs`
- `scoring-signals/src/lib.rs`

## Expected Output

- `docs/cycle-count-report.md`

## Verification

Cycle count report documents total cycles, per-signal breakdown, and feasibility verdict.
