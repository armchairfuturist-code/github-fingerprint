# M002: ZK Proving Layer

**Vision:** Make every GitHub fingerprint score cryptographically provable via zero-knowledge proof — not just server-signed (Ed25519), but verifiable on-chain by any third party without trusting the fingerprint service. The proving pipeline runs async: users get their Ed25519-attested score instantly, while ZK proof generation queues in the background. When the proof lands on Base L2, the credential upgrades to trustless verification.

## Success Criteria

- Rust scoring library produces identical scores to Python reference for the same input
- SP1 zkVM can prove the scoring function with a Groth16 proof output
- Solidity verifier contract deployed on Base testnet
- Async proving queue with Celery/Redis integrated into the API
- Proof status polling endpoint available for clients
- Ed25519 fallback preserved — ZK proving failure never blocks users

## Slices

- [x] **S01: S01** `risk:high` `depends:[]`
  > After this: cargo test passes all signal tests; Python vs Rust comparison shows exact match across all 12 signals for multiple GitHub profiles

- [x] **S02: S02** `risk:high` `depends:[]`
  > After this: Run SP1 prover on sample scoring input, get a valid Groth16 proof in under 5 minutes

- [x] **S03: S03** `risk:medium` `depends:[]`
  > After this: POST /score returns immediately with Ed25519 attestation; proof status endpoint shows in-progress → on_chain

- [x] **S04: S04** `risk:medium` `depends:[]`
  > After this: Verify scoring-sp1-core output matches scoring-core output on identical inputs — analogous to py-scoring-ref/compare.py but Rust-to-Rust

- [x] **S05: S05** `risk:high` `depends:[]`
  > After this: cargo prove build on Linux CI runner, fund deployer wallet, deploy SP1Verifier.sol to Base Sepolia, execute full proof round-trip

## Boundary Map

Not provided.
