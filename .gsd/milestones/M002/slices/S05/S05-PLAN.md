# S05: CI Build + Contract Deployment + E2E Proof Round-Trip

**Goal:** CI builds and tests the full Rust workspace (including SP1 guest program via cargo prove build), Python API, and Node.js contracts; the on-chain proof submission script bridges proof_generated → on_chain; and a run-proof-roundtrip orchestration script chains the full pipeline — ELF build → proof generation → on-chain submission → verification — with dry-run support, so the milestone's E2E loop is ready to execute once the deployer wallet is funded and the contract deployed.
**Demo:** cargo prove build on Linux CI runner, fund deployer wallet, deploy SP1Verifier.sol to Base Sepolia, execute full proof round-trip

## Must-Haves

- 1. `cargo prove build` succeeds inside `scoring-sp1/program/` on Linux CI, producing ELF at expected path
- 2. `cargo build --workspace` compiles all crates including the two newly-added SP1 crates
- 3. `cargo test --workspace` passes for all 8+ crates
- 4. `py -m pytest tests/` passes (286+ tests)
- 5. `node contracts/submit-proof.cjs --help` prints usage and exits 0
- 6. `bash scripts/run-proof-roundtrip.sh --dry-run` prints planned steps and exits 0
- 7. `node tests/test_verifier_contract.cjs` passes (13 contract tests)

## Proof Level

- This slice proves: integration — CI pipeline verifies all builds and tests; E2E orchestration is ready but requires manual wallet funding + Base Sepolia deployment for live execution

## Integration Closure

Upstream surfaces: scoring-sp1/program (guest ELF), scoring-sp1/script (host prover), scoring-sp1-core (ZK engine), scoring-core (reference), scoring-prover-cli (subprocess bridge), api/prover_client.py (Python wrapper), api/proof_tasks.py (Celery task), contracts/SP1Verifier.sol (on-chain verifier). All now buildable and testable in CI with the orchestration script chaining them end-to-end.

## Verification

- CI workflow logs all build/test/prove steps; submit-proof.cjs logs RPC interaction and tx receipt; run-proof-roundtrip.sh prints each step with exit status and timing

## Tasks

- [x] **T01: Add missing crates to workspace and create GitHub Actions CI workflow** `est:1.5h`
  ## Why
  scoring-sp1/program (guest), scoring-sp1/script (host), and scoring-prover-cli (subprocess bridge) are not workspace members — they won't build in CI. The SP1 guest program has never been built outside a local dev machine; `cargo prove build` on Linux CI is the highest-risk step for this milestone.
  - Files: `Cargo.toml`, `.github/workflows/ci.yml`
  - Verify: grep -q "scoring-sp1/program" Cargo.toml && grep -q "cargo prove build" .github/workflows/ci.yml && grep -q "pytest" .github/workflows/ci.yml

- [x] **T02: Create contracts/package.json and submit-proof.cjs for on-chain proof submission** `est:1h`
  ## Why
  The Celery pipeline generates proofs (status reaches `proof_generated`) but has no mechanism to submit them on-chain (transition to `on_chain`). The `submit-proof.cjs` script bridges this gap, reading a Groth16 proof from disk and submitting `verifyProof` to the deployed SP1Verifier contract on Base Sepolia. It must also create `contracts/package.json` so the ethers.js dependency is tracked.
  - Files: `contracts/package.json`, `contracts/submit-proof.cjs`
  - Verify: node contracts/submit-proof.cjs --help 2>&1 | grep -q "Usage" && test -f contracts/package.json

- [x] **T03: Create E2E round-trip orchestration script (run-proof-roundtrip.sh)** `est:1h`
  ## Why
  The slice goal requires a single command that chains the full proof round-trip: build ELF → generate proof → submit on-chain → verify on-chain. The orchestration script connects all pieces so the milestone's E2E loop is executable with one command. It must handle both the live execution path and a `--dry-run` mode for CI/preview.
  - Files: `scripts/run-proof-roundtrip.sh`
  - Verify: bash scripts/run-proof-roundtrip.sh --help 2>&1 | grep -q "Usage" && bash scripts/run-proof-roundtrip.sh --dry-run 2>&1 | grep -q "Step 1"

## Files Likely Touched

- Cargo.toml
- .github/workflows/ci.yml
- contracts/package.json
- contracts/submit-proof.cjs
- scripts/run-proof-roundtrip.sh
