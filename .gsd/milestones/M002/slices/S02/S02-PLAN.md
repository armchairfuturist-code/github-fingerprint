# S02: SP1 Prover Pipeline

**Goal:** Wrap the Rust scoring lib in an SP1 zkVM program, integrate with Succinct Prover Network for proof generation, and output compressed Groth16 proofs ready for on-chain verification.
**Demo:** Run SP1 prover on sample scoring input, get a valid Groth16 proof in under 5 minutes

## Must-Haves

- SP1 zkVM program wrapping the Rust scoring lib compiles to RISC-V
- Succinct Prover Network client integration for proof generation
- Proof generation completes within 5 min for typical inputs
- Proof compressed to Groth16 format
- Cycle count profiling report produced

## Proof Level

- This slice proves: Full — SP1 program builds, prover client generates a proof on testnet, Groth16 proof outputs as a file, cycle count and cost documented

## Integration Closure

Provides Groth16 proofs that S03 verifies on-chain. The proof output format must match SP1 verifier expectations (SP1ProofWithVKey or similar). The prover client is callable from Python through a subprocess/CLI interface for Celery worker integration.

## Verification

- Proof generation status, cycle count, proving time logged. Worker heartbeat for Celery. Prover network response times tracked.

## Tasks

- [x] **T01: Create SP1 zkVM program wrapping scoring lib** `est:2h`
  Create an SP1 zkVM program in scoring-sp1/ that:
  - Depends on the scoring-core lib crate
  - Has an entrypoint that reads serialized ScoreInput from stdin
  - Calls ScoringEngine::score() to produce a ScoreOutput
  - Writes ScoreOutput to stdout (for verification) and commits to the public output stream
  - Executes entirely within the RISC-V guest (no std::fs, no networking)
  - Files: `scoring-sp1/program/*`, `scoring-sp1/script/*`
  - Verify: cargo prove build passes. cargo prove run produces valid output. No std-only dependencies used in program/guest.

- [x] **T02: Prover network integration — generate Groth16 proof** `est:2h`
  Integrate with Succinct Prover Network:
  - Use SP1 SDK to configure a ProverClient pointing to the network
  - Generate a proof via the prover network (testnet first)
  - Handle proof generation errors and retries
  - Output the proof as a serialized Groth16 proof file
  - Files: `scoring-sp1/program/src/main.rs`, `scoring-sp1/script/src/main.rs`, `scoring-prover-cli/src/main.rs`
  - Verify: CLI generates a proof for sample ScoreInput. Proof file is non-empty valid bytes. Proving time and cycle count reported.

- [x] **T03: Python prover client wrapper** `est:1h`
  Create a Python subprocess wrapper in the FastAPI app:
  - run_proof(username: str, score_input: dict) -> dict
  - Calls scoring-prover-cli as subprocess
  - Returns proof metadata (proof_path, cycle_count, proving_time)
  - Files: `api/prover_client.py`
  - Verify: Python subprocess call generates a proof file. Returns correct metadata dict. Error handling works for bad input.

## Files Likely Touched

- scoring-sp1/program/*
- scoring-sp1/script/*
- scoring-sp1/program/src/main.rs
- scoring-sp1/script/src/main.rs
- scoring-prover-cli/src/main.rs
- api/prover_client.py
