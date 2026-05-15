---
estimated_steps: 58
estimated_files: 1
skills_used: []
---

# T03: Create E2E round-trip orchestration script (run-proof-roundtrip.sh)

## Why
The slice goal requires a single command that chains the full proof round-trip: build ELF → generate proof → submit on-chain → verify on-chain. The orchestration script connects all pieces so the milestone's E2E loop is executable with one command. It must handle both the live execution path and a `--dry-run` mode for CI/preview.

## Files
- `scripts/run-proof-roundtrip.sh` — new orchestration script

## Do

1. **Create `scripts/` directory** if it doesn't exist

2. **Create `scripts/run-proof-roundtrip.sh`** with:

   **CLI Interface**:
   ```bash
   Usage: ./scripts/run-proof-roundtrip.sh [options]
   
   Options:
     --fixture <path>         ScoreInput fixture (default: scoring-sp1/fixtures/sample_profile.json)
     --elf-path <path>        ELF path (default: scoring-sp1/program/elf/riscv32im-succinct-zkvm-elf)
     --prover-mode <local|network>  SP1 prover mode (default: local)
     --rpc-url <url>          Base Sepolia RPC
     --contract <address>     SP1Verifier contract address
     --dry-run                Print planned steps without executing
     --clean                  Delete stale ELF and proof before starting
     --help                   Show usage
   ```

   **Execution steps (when not --dry-run)**:
   1. Check prerequisites: `cargo`, `cargo-prove`, `sp1up`, `node`, `docker` (for groth16)
   2. If --clean, rm -f ELF and proof.bin
   3. `cd scoring-sp1/program && cargo prove build && cd ../..`
   4. Verify ELF exists at expected path
   5. `cargo build -p scoring-sp1-script --release` (or use existing binary)
   6. `cargo run -p scoring-sp1-script --release -- --input $FIXTURE`
   7. Verify proof.bin was generated
   8. `node contracts/submit-proof.cjs --proof proof.bin [--contract ...] [--rpc-url ...]`
   9. Print summary: ELF size, proof size, tx hash, gas used, verification result

   **Each step prints**:
   ```
   [1/9] → Step name...
   [1/9] ✔ Step name (duration: Xs)
   ```
   or
   ```
   [1/9] ✗ Step name (error: ...)
   ```

   **Error handling**:
   - `set -e` at top to stop on first failure
   - Each step captures exit code and prints it
   - If a step fails, print the error and exit with the step's exit code
   - `trap` to clean up temp files on exit
   - If docker not available for groth16, print warning but continue (will use CPU proving which may timeout)

   **Dry-run mode**:
   - Print each step name and what it would do
   - Check prerequisite availability (which cargo, which node, etc.)
   - Check ELF staleness (mtime of source vs ELF)
   - Print estimated durations
   - Exit 0

3. **Make the script executable**: `chmod +x scripts/run-proof-roundtrip.sh`

## Must-haves
- --dry-run mode prints all planned steps and checks prerequisites
- Each step prints clear status (✔ or ✗) with timing
- ELF is rebuilt if --clean flag given
- Error in any step stops the pipeline and prints the error

## Inputs

- `scoring-sp1/program/Cargo.toml`
- `scoring-sp1/script/src/main.rs`
- `contracts/submit-proof.cjs`
- `contracts/deploy.cjs`
- `contracts/deployed-address.txt`

## Expected Output

- `scripts/run-proof-roundtrip.sh`

## Verification

bash scripts/run-proof-roundtrip.sh --help 2>&1 | grep -q "Usage" && bash scripts/run-proof-roundtrip.sh --dry-run 2>&1 | grep -q "Step 1"
