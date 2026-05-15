---
estimated_steps: 11
estimated_files: 3
skills_used: []
---

# T02: Prover network integration — generate Groth16 proof

Integrate with Succinct Prover Network:
- Use SP1 SDK to configure a ProverClient pointing to the network
- Generate a proof via the prover network (testnet first)
- Handle proof generation errors and retries
- Output the proof as a serialized Groth16 proof file

Create a CLI wrapper (scoring-prover-cli) that:
- Reads ScoreInput JSON
- Generates proof via prover network
- Writes proof to stdout or file
- Outputs proof metadata (cycle count, proving time, proof size)

Output: Proof generates successfully on testnet. CLI outputs valid Groth16 proof.

## Inputs

- `SP1 SDK docs`
- `Succinct Prover Network docs`

## Expected Output

- `scoring-sp1/program/src/main.rs (updated)`
- `scoring-sp1/script/src/main.rs (updated)`
- `scoring-prover-cli/src/main.rs`

## Verification

CLI generates a proof for sample ScoreInput. Proof file is non-empty valid bytes. Proving time and cycle count reported.
