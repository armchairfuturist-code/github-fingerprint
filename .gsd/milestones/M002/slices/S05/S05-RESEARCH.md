# S05 Research: CI Build + Contract Deployment + E2E Proof Round-Trip

**Date:** 2026-05-12

## Summary

S05 is the integration and delivery capstone for Milestone M002. It has three independent work streams: (1) a Linux-based GitHub Actions CI that builds the SP1 ELF with `cargo prove build`, runs all Rust/Python/contract tests, and produces the scoring-prover-cli binary; (2) funding the generated deterministic wallet (~0.01 Base Sepolia ETH) and deploying `SP1Verifier.sol` to Base Sepolia; (3) writing an E2E orchestration script that chains the full proof round-trip — ELF build → proof generation → on-chain submission → on-chain verification — then executing it against the deployed contract.

All prerequisite artifacts exist: the scoring-sp1 guest program, the SP1 host script, the verifier contract with ABI and bytecode, the deploy script, the deterministic wallet, the Celery/Redis async queue, and the proof status API. The missing pieces are CI automation, wallet funding, a proof-submission step, and the orchestration wiring that connects them.

## Recommendation

Build in two phases:

1. **CI Workflow (GitHub Actions)** — Create `.github/workflows/ci.yml` targeting `ubuntu-latest` (SP1's RISC-V toolchain is Linux/macOS only; Windows is unsupported). Install Rust 1.91.0, install SP1 toolchain via `sp1up`, cache `~/.cargo` and `~/.sp1/circuits`, run `cargo prove build` in `scoring-sp1/program/`, run scoring-cross-compare, run Python tests, run Node.js contract tests. Add the `scoring-prover-cli` crate to the workspace or build it separately in CI.

2. **E2E Orchestration Script + Contract Submission** — Write a single `scripts/run-proof-roundtrip.sh` (or `scripts/run-proof-roundtrip.cjs`) that: runs `cargo prove build` if the ELF is stale, invokes `scoring-sp1-script` on a fixture, generates a Groth16 proof, writes a `submitProof` transaction to the deployed contract on Base Sepolia, and calls `verifyProof` to confirm. Write a `contracts/submit-proof.cjs` script for the on-chain submission step (which is the current gap — the Celery pipeline generates proofs but has no auto-submit to chain).

## Implementation Landscape

### Key Files

- **`.github/workflows/ci.yml`** — New file. GitHub Actions CI definition for Linux build + test matrix.
- **`contracts/submit-proof.cjs`** — New file. Submits a Groth16 proof to the deployed SP1Verifier contract on Base Sepolia. Reads proof bytes from disk, encodes the call to `verifyProof` via ethers.js, sends the transaction. (Alternative: the existing `ProofStatusStore` already has an `on_chain` status — this script fills that transition.)
- **`scripts/run-proof-roundtrip.sh`** — New file. Bash orchestration: builds ELF, generates proof, submits to chain, verifies.
- **`Cargo.toml`** — Modify: add `scoring-prover-cli` and `scoring-sp1/{program,script}` workspace members so CI builds them together.
- **`scoring-sp1/script/src/main.rs`** — Already exists. Host script that reads a fixture, proves via SP1 SDK, saves proof.bin. Needs minor polish: it currently uses hardcoded paths for ELF and output; should accept them as args or env vars for CI flexibility.
- **`contracts/deploy.cjs`** — Already exists. Needs wallet funding (`0x7d373839eb87DEED431832CFeF8A76c10ed2E87A` with ~0.01 Base Sepolia ETH), then works as-is.
- **`scoring-sp1/program/elf/riscv32im-succinct-zkvm-elf`** — Output path for `cargo prove build`. The host script reads from this path by default.
- **`tests/test_proving_e2e.py`** — Already exists, 22 tests with mocked deps. In CI, these should be run against a real (or fully mocked) proving pipeline.

### Build Order

1. **CI workflow first** — unblocks everything. Without CI, we can't verify that `cargo prove build` works or that integration tests pass on Linux. The SP1 toolchain install (sp1up) is the highest-risk step — it involves network downloads, GitHub rate limiting, and Docker dependency. CI also validates that the scoring-sp1 program compiles to RISC-V.

2. **Wallet funding & contract deployment** — independent of CI setup. Fund the deterministic deployer wallet (`0x7d373839eb87DEED431832CFeF8A76c10ed2E87A`) from a Base Sepolia faucet (~$0 in real value, ~0.01 test ETH). Then run `PRIVATE_KEY=0x... node contracts/deploy.cjs`. This writes `deployed-address.txt` with the on-chain address.

3. **Proof submission script** (`contracts/submit-proof.cjs`) — requires the contract address from step 2. Writes the parity closure: the Celery pipeline can set status to `proof_generated` but needs this script to bridge to `on_chain`.

4. **E2E round-trip orchestration** (`scripts/run-proof-roundtrip.sh`) — requires all prior steps. Chains: build ELF → generate proof → submit on-chain → verify. The final verification confirms the complete pipeline works.

### Verification Approach

1. **CI workflow verifies**: `cargo prove build` outputs ELF at expected path; scoring-cross-compare passes zero-diff for all 3 fixtures; all 286+ Python tests pass; `cargo check` works for all workspace members
2. **Contract deployment verifies**: `deploy-receipt.json` written with tx hash and block number; deployed address is a valid hex address; `node tests/test_verifier_contract.cjs` passes (already passes without deployment)
3. **Proof round-trip verifies**: ELF builds → proof generates → submission succeeds (tx receipt) → `verifyProof` call returns true on-chain
4. **E2E dry run**: `scripts/run-proof-roundtrip.sh --dry-run` prints the planned steps without executing on-chain calls

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| SP1 toolchain install in CI | `sp1up` + `~/.sp1/bin/sp1up` | Official SP1 installer; handles RISC-V toolchain, `cargo-prove` CLI, and circuit artifacts |
| Rust caching in CI | `actions/cache@v3` with `~/.cargo` and `~/.sp1/circuits` | SP1 CI docs recommend this pattern; dramatically speeds up subsequent runs |
| Ethereum interaction | `ethers.js` | Already used in `deploy.cjs`, `setup-wallet.cjs`, and `test_verifier_contract.cjs`. Consistent toolchain. |
| Wallet generation | `ethers.HDNodeWallet.fromSeed()` | Already used in `setup-wallet.cjs`. Deterministic from fixed seed. |

## Constraints

- **SP1 toolchain is Linux/macOS only** — `cargo prove build` requires RISC-V compilation target that doesn't exist on Windows. CI runner must be `ubuntu-latest` or `macos-latest`.
- **Docker requirement** — SP1 Groth16 proof generation uses Docker for gnark proving. CI runners need Docker installed and running (GitHub Actions `ubuntu-latest` has Docker pre-installed).
- **Circuit artifacts download** — First `cargo prove build` or proof generation downloads ~500MB+ of circuit artifacts to `~/.sp1/circuits/groth16/`. Cache these aggressively.
- **Deployer wallet private key is in plaintext** — The deterministic wallet's private key is in `contracts/deploy-wallet.json` and `contracts/deployed-address.txt`. For CI, use GitHub Actions secrets. For local deployment, the key is already on disk — acceptable for testnet.
- **Base Sepolia RPC may be slow or rate-limited** — `https://sepolia.base.org` is the public RPC. Consider using Alchemy/Infura for reliability.
- **scoring-prover-cli and scoring-sp1 crates NOT in workspace members** — The root `Cargo.toml` does not list them. Need to add them or handle separately in CI.

## Common Pitfalls

- **`sp1up` GitHub rate limiting** — SP1 CI docs note rate limits for unauthenticated requests to GitHub API. Use `--token "${{ secrets.GH_PAT }}"` with a fine-grained PAT to avoid.
- **Rust version mismatch** — SP1 v6 requires Rust 1.91.0. The `scoring-sp1-core` crate uses `#![no_std]` and `#![no_main]` — a newer Rust may have different alloc/panic behavior. Pin the version explicitly.
- **`cargo prove build` must run INSIDE `scoring-sp1/program/`** — The CLI only works when run in the program directory (see succinctlabs/sp1#248). CI steps must `cd scoring-sp1/program && cargo prove build`.
- **ELF path in the host script** — `scoring-sp1/script/src/main.rs` defaults to `program/elf/riscv32im-succinct-zkvm-elf` relative to CWD. CI must run the script from `scoring-sp1/` or set `SP1_ELF_PATH`.
- **`scoring-prover-cli` subprocess path** — The CLI calls `scoring-sp1-script` as a subprocess. CI must either install the binary to PATH or set `SP1_SCRIPT_PATH`.
- **Docker not available in some CI contexts** — Standard GitHub Actions `ubuntu-latest` includes Docker. Self-hosted runners may not. Verify before CI setup.
- **Python test path issue** — Running `pytest` bare fails with `ModuleNotFoundError`. Must use `python -m pytest` (pre-existing issue, documented in S04 summary).

## Open Risks

- **`cargo prove build` may fail with compilation errors** on a fresh Linux environment. The scoring-sp1 guest program uses `sp1-zkvm` v6 and `scoring-sp1-core` as a dependency. Any mismatched SP1 API surfaces could break the build — the ELF has never been built in CI before.
- **Circuits download time** — First CI run may take 10-20 minutes due to artifact downloads. Cache hit rate on subsequent runs determines viability.
- **Proof generation time in CI** — Local CPU proving (the default) can take several minutes for Groth16. CI timeout may need to be generous (30+ min). Consider using Succinct Prover Network (SP1_PROVER=network) for faster CI proofs, but that requires API credentials.
- **Base Sepolia wallet funding** — Faucets are unreliable. May need to request from multiple faucets or use a bridge from Sepolia ETH. The wallet address `0x7d373839eb87DEED431832CFeF8A76c10ed2E87A` has never been funded — this is a manual blocking step.
- **On-chain `verifyProof` may fail** even with a correctly generated proof, if there's a version mismatch between the SP1 verifier contract and the SP1 SDK used to generate the proof. Both use v6, but sub-version compatibility needs verification.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| SP1 zkVM (Succinct) | — | Not installed. Core technology — `cargo prove build`, SP1 SDK v6, Prover Network. Documentation at docs.succinct.xyz |
| Base Sepolia (EVM) | — | Not installed. Standard EVM; ethers.js handles interaction. |
| GitHub Actions | — | Not installed. Standard CI; patterns well-documented. |

## Sources

- SP1 CI setup: install `sp1up`, cache `~/.cargo` and `~/.sp1/circuits`, use Rust 1.91.0. Rate limiting can be mitigated with GH_PAT token. (source: [Usage in CI — Succinct Docs](https://docs.succinct.xyz/docs/sp1/developers/usage-in-ci))
- SP1 installation: `curl -L https://sp1up.succinct.xyz | bash`, then `~/.sp1/bin/sp1up`. Requires git, Rust, Docker, protoc. (source: [Installation — Succinct Docs](https://docs.succinct.xyz/docs/sp1/getting-started/install))
- SP1 is Linux/macOS only — no Windows support for `cargo prove build`. (source: [SP1 Issues #248](https://github.com/succinctlabs/sp1/issues/248))
- `cargo prove build` must run inside the program directory. SP1 SDK v6 uses `ProverClient::new()` for CPU mode and `SP1_PROVER=network` for Prover Network. (source: [SP1 Quickstart](https://docs.succinct.xyz/docs/sp1/getting-started/quickstart))
