---
depends_on: [M001]
---

# M002: ZK Proving Layer (DRAFT)

**Status:** Draft — refine before executing

## Seed Material

### Architecture
- **Proving:** SP1 zkVM (Succinct) — scoring function ported to Rust, compiled to RISC-V, proven by SP1 Hypercube
- **Verification:** Base L2 — Solidity verifier contract, ~$0.008/proof
- **Async pattern:** Profile returned immediately with Ed25519 attestation (from M001). ZK proof generated async. Ed25519 fallback always available.
- **Prover:** Succinct Prover Network for initial production. Local GPU proving deferred (R019).

### Key Decisions (from M001 discussion)
- SP1 over RISC Zero for lower cost ($0.02-0.10 vs $0.04-0.17) and faster proving (~2 min)
- Base over Arbitrum for lower verification cost ($0.008 vs $0.04)
- Rust port of scoring function — must support weight/parameter updates without circuit redeployment
- Proving is async + queued — user experience never blocks on prover

### Provisional Slices
- S01: Rust Scoring Library — Port all signals + role-adaptive weights to Rust. lib crate with serde input/output. CI comparison against Python reference.
- S02: SP1 Prover Pipeline — zkVM program wrapping the Rust scoring lib. Prover client integration. Proof generation + Groth16 compression.
- S03: Base Verifier Contract — Solidity verifier deployment. Integration into the API with async queue (Celery/Redis). Ed25519 fallback wiring. Proof status polling endpoint.

### Open Questions
- Prover network reliability in production — do we also need a backup prover?
- Gas optimization for different depth tiers — each tier proves a different subset of signals
- Prover cost at scale — $0.03-0.11/proof target; what actual throughput on Succinct's network?
- How to version the verifier contract when the scoring function changes?

### Technical Assumptions (VERIFY before CONTEXT.md)
- SP1 can prove the Rust scoring function at reasonable cycle count (~10-50k constraints equivalent)
- Base verifier contract integration is straightforward (SP1 provides templates)
- Succinct Prover Network is available and cost-predictable for our workload
