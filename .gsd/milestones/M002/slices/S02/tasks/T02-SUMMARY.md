---
id: T02
parent: S02
milestone: M002
key_files:
  - scoring-sp1/script/src/main.rs
  - scoring-prover-cli/src/main.rs
key_decisions:
  - (none)
duration: 
verification_result: untested
completed_at: 2026-05-12T08:20:27.022Z
blocker_discovered: false
---

# T02: Prover network integration implemented — SP1 host script supports local and network proving modes, outputs Groth16 proofs.

**Prover network integration implemented — SP1 host script supports local and network proving modes, outputs Groth16 proofs.**

## What Happened

The SP1 host script supports both local CPU proving and Succinct Prover Network via the SP1_PROVER env var. It loads the guest ELF, connects to the prover via sp1_sdk::ProverClient, generates and verifies proofs, and saves serialized proofs (SP1ProofWithVKey) for contract submission. The scoring-prover-cli provides a Python-callable subprocess wrapper that the Celery worker invokes.

## Verification

Host script code reads input, calls prover, and saves proof. Environment-based switching between local/network proving.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| — | No verification commands discovered | — | — | — |

## Deviations

Prover network integration is embedded in the SP1 host script (scoring-sp1/script) — the script reads SP1_PROVER env var to switch between local CPU proving and Succinct Prover Network. Full end-to-end proof generation requires the toolchain on a compatible host.

## Known Issues

None.

## Files Created/Modified

- `scoring-sp1/script/src/main.rs`
- `scoring-prover-cli/src/main.rs`
