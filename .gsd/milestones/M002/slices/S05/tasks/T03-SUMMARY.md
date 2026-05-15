---
id: T03
parent: S05
milestone: M002
key_files:
  - scripts/run-proof-roundtrip.sh
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-05-12T10:03:14.206Z
blocker_discovered: false
---

# T03: Created scripts/run-proof-roundtrip.sh — E2E orchestration script that chains ELF build → proof generation → on-chain submission → verification with --dry-run and --clean support

**Created scripts/run-proof-roundtrip.sh — E2E orchestration script that chains ELF build → proof generation → on-chain submission → verification with --dry-run and --clean support**

## What Happened

Created the scripts/ directory and scripts/run-proof-roundtrip.sh orchestration script that chains the full proof round-trip pipeline in 9 steps:

1. Check prerequisites (cargo, cargo-prove, sp1up, node, docker, openssl)
2. Clean stale artifacts if --clean flag is given
3. Build SP1 guest ELF (cd scoring-sp1/program && cargo prove build)
4. Verify ELF exists at expected path with size display
5. Build SP1 host script in release mode (cargo build -p scoring-sp1-script --release)
6. Generate proof (cargo run -p scoring-sp1-script --release -- --input $FIXTURE) with SP1_ELF_PATH and SP1_PROOF_OUTPUT env vars set
7. Verify proof.bin was generated
8. Submit proof on-chain via node contracts/submit-proof.cjs with --proof, --rpc-url, and optional --contract arguments
9. Print summary of ELF size, proof size, prover mode, and contract info

CLI options: --fixture, --elf-path, --prover-mode, --rpc-url, --contract, --dry-run, --clean, --help. Each step prints [N/9] → step name with timing, ✔ on success, ✗ on failure. Dry-run mode checks all prerequisites, reports ELF staleness, fixture existence, prints estimated durations, and exits 0. Error handling via set -euo pipefail, trap cleanup for temp files, and per-step exit code capture. The script properly maps --prover-mode to the SP1_PROVER env var consumed by scoring-sp1-script, and sets SP1_ELF_PATH to the absolute path of the ELF so the host script can find it regardless of CWD.

## Verification

--help displays Usage text and exits 0. --dry-run displays all planned steps with "Step 1" in output and checks prerequisites. Shell syntax validated with bash -n (no errors). The script is executable and handles both Linux and macOS stat formats for file size/mtime queries.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `bash scripts/run-proof-roundtrip.sh --help 2>&1 | grep -q "Usage"` | 0 | ✅ pass | 200ms |
| 2 | `bash scripts/run-proof-roundtrip.sh --dry-run 2>&1 | grep -q "Step 1"` | 0 | ✅ pass | 300ms |
| 3 | `bash -n scripts/run-proof-roundtrip.sh` | 0 | ✅ pass | 50ms |

## Deviations

None.

## Known Issues

Scoring fixture scoring-sp1/fixtures/sample_profile.json does not exist yet — the script warns about this in dry-run mode and will fail at step 6 if the fixture is not provided via --fixture. This is expected at this point in the milestone as fixture generation may be part of a prior step or external setup.

## Files Created/Modified

- `scripts/run-proof-roundtrip.sh`
