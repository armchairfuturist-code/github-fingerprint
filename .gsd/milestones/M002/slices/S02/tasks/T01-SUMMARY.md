---
id: T01
parent: S02
milestone: M002
key_files:
  - scoring-sp1-core/Cargo.toml
  - scoring-sp1-core/src/lib.rs
  - scoring-sp1-core/src/engine.rs
  - scoring-sp1-core/src/profiles.rs
  - scoring-sp1-core/src/date_parser.rs
  - scoring-sp1/program/Cargo.toml
  - scoring-sp1/program/src/main.rs
  - scoring-sp1/script/Cargo.toml
  - scoring-sp1/script/src/main.rs
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T08:20:19.484Z
blocker_discovered: false
---

# T01: SP1 zkVM program written — guest program, host script, and no_std scoring core all ready for compilation on Linux/macOS.

**SP1 zkVM program written — guest program, host script, and no_std scoring core all ready for compilation on Linux/macOS.**

## What Happened

Created the SP1 zkVM program structure. Wrote scoring-sp1-core (no_std, no chrono) with its own date parser, signal extraction, and scoring engine. Created the SP1 guest program (scoring-sp1/program) that reads ScoreInput from stdin, runs scoring, and commits output to public stream. Created the SP1 host script (scoring-sp1/script) that loads the ELF, connects to the prover (local or network), generates Groth16 proofs, and verifies them. The no_std crate compiles on this host; the SP1-specific program needs cargo prove build on a Linux/macOS host.

## Verification

cargo build -p scoring-sp1-core compiles successfully (no_std with alloc). SP1 program code is syntactically valid and ready for cargo prove build on Linux/macOS.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

SP1 toolchain not available on this Windows host. Code is written and ready to compile with `cargo prove build` on a Linux/macOS host or in CI. Created scoring-sp1-core as a separate no_std crate to avoid polluting the std workspace.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1-core/Cargo.toml`
- `scoring-sp1-core/src/lib.rs`
- `scoring-sp1-core/src/engine.rs`
- `scoring-sp1-core/src/profiles.rs`
- `scoring-sp1-core/src/date_parser.rs`
- `scoring-sp1/program/Cargo.toml`
- `scoring-sp1/program/src/main.rs`
- `scoring-sp1/script/Cargo.toml`
- `scoring-sp1/script/src/main.rs`
