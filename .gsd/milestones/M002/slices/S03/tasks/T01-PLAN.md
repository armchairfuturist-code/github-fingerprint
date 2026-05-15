---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T01: Deploy SP1 verifier contract on Base Sepolia

Use SP1's Solidity verifier template:
- Run `cargo prove deploy` or SP1's forge template to generate verifier contract
- Deploy to Base Sepolia testnet
- Verify contract on Base Sepolia explorer
- Save deployed contract address and ABI

Output: Deployed verifier contract address. ABI file saved. Verification on block explorer.

## Inputs

- `SP1 Solidity verifier template`
- `scoring-sp1 proof output format`

## Expected Output

- `contracts/SP1Verifier.sol`
- `contracts/deployed-address.txt`
- `contracts/abi/SP1Verifier.json`

## Verification

Contract verified on Base Sepolia explorer. Test: submit a known-valid Groth16 proof → verification passes. Test: submit invalid proof → verification fails.
