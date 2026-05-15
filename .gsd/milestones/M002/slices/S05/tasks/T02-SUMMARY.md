---
id: T02
parent: S05
milestone: M002
key_files:
  - contracts/package.json
  - contracts/submit-proof.cjs
key_decisions:
  - Used ethers.staticCall for verifyProof since SP1Verifier.verifyProof is a view function — no state-changing transaction is needed.
  - Bincode proof parsing extracts programVKey from last 32 bytes of SP1ProofWithVKey (SP1VerificationKey.hash) and builds proofBytes from curve points + public inputs.
  - Path resolution handles both normalized Windows paths and Unix-style /tmp paths (Git Bash compatibility).
duration: 
verification_result: passed
completed_at: 2026-05-12T09:59:18.685Z
blocker_discovered: false
---

# T02: Created contracts/submit-proof.cjs with CLI proof submission and updated contracts/package.json to ethers@^6.13.0

**Created contracts/submit-proof.cjs with CLI proof submission and updated contracts/package.json to ethers@^6.13.0**

## What Happened

Task T02 created the on-chain proof submission script that bridges the Celery pipeline's proof_generated status to on-chain verification via the SP1Verifier contract on Base Sepolia.

The contracts/package.json was updated from scoring-contracts/ethers@^6.9.0 to github-fingerprint-contracts/ethers@^6.13.0, and npm install was run to regenerate package-lock.json.

The submit-proof.cjs script provides a full CLI interface with --proof, --rpc-url, --contract, --vkey, --public-inputs, --dry-run, and --help options. It reads bincode-serialized SP1ProofWithVKey proof files, extracting the programVKey from the last 32 bytes of the file (SP1VerificationKey.hash) and the Groth16 proof bytes from the curve points and public inputs. The contract address is resolved from contracts/deployed-address.txt with proper handling of the not-yet-deployed sentinel value.

Edge cases handled: missing proof.bin file (exit 1), RPC unreachable (exit 1), contract call revert with decoded reason (exit 1), no PRIVATE_KEY env var (exit 1), invalid contract address (exit 1), and not-yet-deployed state (exit 1 with deploy instructions). The dry-run mode prints the submission plan without sending a transaction.

Since the SP1Verifier's verifyProof is a view function (no state change), the script uses ethers.Contract.staticCall for verification rather than sending a transaction. On success it prints the contract address, verification key, estimated gas, and duration; on revert it decodes and displays the revert reason.

## Verification

--help displays Usage text and exits 0. package.json exists with correct name and ethers dependency. npm install succeeds. Missing proof file exits 1 with clear error. Missing PRIVATE_KEY exits 1 with error. not-yet-deployed in address file exits 1 with deploy instructions. Invalid contract address is rejected. Dry-run with a valid proof file prints the submission plan and exits 0.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `node contracts/submit-proof.cjs --help 2>&1 | grep -q Usage` | 0 | ✅ pass | 200ms |
| 2 | `test -f contracts/package.json` | 0 | ✅ pass | 50ms |
| 3 | `npm install in contracts/` | 0 | ✅ pass | 1500ms |
| 4 | `Missing proof file error handling` | 1 | ✅ pass (expected exit 1) | 100ms |
| 5 | `not-yet-deployed address error handling` | 1 | ✅ pass (expected exit 1) | 100ms |
| 6 | `Dry-run with valid mock proof` | 0 | ✅ pass | 200ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `contracts/package.json`
- `contracts/submit-proof.cjs`
