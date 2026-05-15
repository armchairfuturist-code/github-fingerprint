# S05: CI Build + Contract Deployment + E2E Proof Round-Trip — UAT

**Milestone:** M002
**Written:** 2026-05-12T10:06:22.845Z

# UAT: CI Build + Contract Deployment + E2E Proof Round-Trip

## Preconditions
- GitHub repository has CI enabled
- Secrets configured: GH_PAT (for SP1 toolchain rate limiting)
- Node.js 20+ available for contract tests
- Deployer wallet funded on Base Sepolia (for live execution)

## UAT-01: CI Workflow Passes (Rust Stage)
**Type:** Automated (CI pipeline)

1. Push a commit to `main` or open a PR against `main`
2. Navigate to Actions tab → CI workflow
3. Verify the `Rust Build & Test` stage starts
4. **Expected:** SP1 toolchain installs, `cargo prove build` succeeds, `cargo build --workspace` succeeds, `cargo test --workspace` passes all tests
5. **Expected:** SP1 circuits cache is used on subsequent runs (cache hit)

## UAT-02: CI Workflow Passes (Python Stage)
**Type:** Automated (CI pipeline)

1. From the same CI run, verify the `Python Tests` stage starts
2. **Expected:** Python 3.12 is set up with pip cache, `pip install -r requirements.txt` succeeds
3. **Expected:** `python -m pytest tests/` passes with exit code 0

## UAT-03: CI Workflow Passes (Contract Stage)
**Type:** Automated (CI pipeline)

1. From the same CI run, verify the `Contract Tests` stage starts
2. **Expected:** Node.js 20 is set up, `npm ci` succeeds in contracts/
3. **Expected:** `node tests/test_verifier_contract.cjs` passes 13 test cases

## UAT-04: submit-proof.cjs CLI Help
**Type:** Manual / Local

1. Run `node contracts/submit-proof.cjs --help`
2. **Expected:** Prints usage instructions and exits 0

## UAT-05: submit-proof.cjs Error Handling
**Type:** Manual / Local

1. Run `node contracts/submit-proof.cjs` without PRIVATE_KEY set
2. **Expected:** Exits 1 with error message about missing PRIVATE_KEY
3. Run without a proof file
4. **Expected:** Exits 1 with clear error message

## UAT-06: run-proof-roundtrip.sh Dry-Run
**Type:** Manual / Local (bash available)

1. Run `bash scripts/run-proof-roundtrip.sh --dry-run`
2. **Expected:** Prints all 9 planned steps with timing estimates, checks prerequisites, exits 0
3. Run `bash scripts/run-proof-roundtrip.sh --help`
4. **Expected:** Prints usage and exits 0

## UAT-07: Live E2E Round-Trip (Manual)
**Type:** Manual — requires funded wallet + deployed contract

1. Deploy SP1Verifier.sol to Base Sepolia, write address to contracts/deployed-address.txt
2. Set PRIVATE_KEY environment variable
3. Run `bash scripts/run-proof-roundtrip.sh --fixture <path-to-fixture> --rpc-url https://sepolia.base.org`
4. **Expected:** ELF builds, proof generates, proof is submitted on-chain, verification returns success
5. **Expected:** Summary printed with ELF size, proof size, verification timing

## Edge Cases

- **No PRIVATE_KEY:** submit-proof.cjs exits 1 with clear instructions
- **Not-yet-deployed contract:** submit-proof.cjs reads deployed-address.txt sentinel, exits 1 with deployment instructions
- **RPC unreachable:** submit-proof.cjs exits 1 with decoded error
- **Proof file missing:** submit-proof.cjs exits 1 with file-not-found error
- **Missing fixture:** run-proof-roundtrip.sh warns about missing fixture and exits at step 6
- **Stale ELF:** --clean flag deletes old ELF/proof before starting

## Not Proven By This UAT
- Full proof generation on GPU-accelerated CI runners (requires SP1 network prover)
- Live contract deployment (requires manual Base Sepolia deployment)
- Cross-browser contract interaction verification
