---
estimated_steps: 39
estimated_files: 2
skills_used: []
---

# T02: Create contracts/package.json and submit-proof.cjs for on-chain proof submission

## Why
The Celery pipeline generates proofs (status reaches `proof_generated`) but has no mechanism to submit them on-chain (transition to `on_chain`). The `submit-proof.cjs` script bridges this gap, reading a Groth16 proof from disk and submitting `verifyProof` to the deployed SP1Verifier contract on Base Sepolia. It must also create `contracts/package.json` so the ethers.js dependency is tracked.

## Files
- `contracts/package.json` — new, with ethers dependency
- `contracts/submit-proof.cjs` — new submission script

## Do

1. **Create `contracts/package.json`**:
   - name: `github-fingerprint-contracts`
   - dependencies: `ethers@^6.13.0`

2. **Create `contracts/submit-proof.cjs`** with these capabilities:

   **CLI Interface**:
   ```
   node contracts/submit-proof.cjs [options]
   
   Options:
     --proof <path>        Path to proof.bin (default: proof.bin)
     --rpc-url <url>       Base Sepolia RPC (default: https://sepolia.base.org)
     --contract <address>  SP1Verifier contract address (reads from deployed-address.txt if omitted)
     --vkey <hex>          Program verification key (default: from SP1_VKEY env or hardcoded test VKey)
     --public-inputs <hex> Hex-encoded public inputs (optional)
     --dry-run             Print plan without sending transaction
     --help                Show usage
   ```

   **Behavior**:
   - Read proof.bin (bincode-serialized SP1ProofWithVKey)
   - Read contract address from `contracts/deployed-address.txt` if `--contract` not provided
   - If address file contains 'not-yet-deployed' or address is 0x0, print clear error and exit 1
   - Connect to Base Sepolia RPC via ethers.JsonRpcProvider
   - Decode the proof into the 3 verifyProof params: programVKey, publicValues, proofBytes
   - Call `verifyProof(programVKey, publicValues, proofBytes)` on SP1Verifier contract
   - On success: print tx hash, block number, gas used
   - On revert: decode revert reason and print it
   - --dry-run: print what would be done, don't send tx

   **Edge cases**:
   - proof.bin file missing → exit 1 with clear error
   - RPC unreachable → exit 1 with error
   - Contract call reverts → decode reason, exit 1
   - No PRIVATE_KEY env var → exit 1 with error

3. **Run `npm install`** in `contracts/` to generate `package-lock.json` and test the script loads

## Inputs

- `contracts/deploy.cjs`
- `contracts/deployed-address.txt`
- `contracts/abi/SP1Verifier.json`
- `contracts/deploy-wallet.json`

## Expected Output

- `contracts/package.json`
- `contracts/submit-proof.cjs`

## Verification

node contracts/submit-proof.cjs --help 2>&1 | grep -q "Usage" && test -f contracts/package.json
