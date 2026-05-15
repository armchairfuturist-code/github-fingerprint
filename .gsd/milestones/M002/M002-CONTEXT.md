---
depends_on: [M001]
---

# M002: ZK Proving Layer

**Status:** Ready for execution

## Vision

Make every GitHub fingerprint score cryptographically provable via zero-knowledge proof — not just server-signed (Ed25519), but verifiable on-chain by any third party without trusting the fingerprint service. The proving pipeline runs async: users get their Ed25519-attested score instantly (from M001), while ZK proof generation queues in the background. When the proof lands on Base L2, the credential upgrades to trustless verification. The Ed25519 fallback always remains valid.

## Architecture

- **Scoring lib (Rust):** Port the entire Python scoring engine (12 signals, role-adaptive weights, confidence thresholding) to a Rust library crate. Serialization via serde JSON. Must support weight/parameter updates without full circuit redeployment — parameters are program inputs, not compiled constants.
- **Proving (SP1 zkVM):** The Rust scoring lib compiled to RISC-V and proven by SP1 Hypercube. Prover client connects to Succinct Prover Network for production proving (~2 min, $0.02-0.10/proof). Proof compressed to Groth16 for on-chain verification.
- **Verification (Base L2):** Solidity verifier contract deployed on Base. ~$0.008/proof verification cost. SP1 provides verifier templates — integration is straightforward.
- **Async queue (Celery/Redis):** Proof generation is async + queued. API returns Ed25519-attested score immediately. Background worker picks up the proving job, generates the proof, submits to Base. Proof status polling endpoint for clients.
- **Ed25519 fallback (from M001):** Always available. If ZK proving fails at any step, the Ed25519 attestation remains the valid credential.

## Key Decisions

- SP1 over RISC Zero: lower cost ($0.02-0.10 vs $0.04-0.17), faster proving (~2 min)
- Base over Arbitrum: lower verification cost ($0.008 vs $0.04)
- Proving is async + queued — user experience never blocks on prover
- Succinct Prover Network for initial production (local GPU proving deferred)
- Scoring parameters are program inputs (not compile-time constants) so weight updates don't require circuit redeployment
- Ed25519 attestation remains the instant safety net — ZK is an upgrade, not a gate

## Open Questions

- Prover network reliability — do we need a backup prover?
- Gas optimization across different depth tiers
- Prover cost at scale — verify actual throughput on Succinct's network
- Verifier contract versioning strategy when scoring function changes
