# ZK Research Log — Phase 2 Roadmap

**Date:** 2026-04-29  
**Path:** B → Full ZK trustlessness  
**Status:** Pre-research (before committing to a ZK stack)

## Research Agenda

### 1. Noir (https://noir-lang.org)

A ZK domain-specific language with Python-friendly syntax.

**Why it fits this project:**
- Noir circuits can prove arbitrary computation — e.g., "this score was correctly computed from this GitHub data without revealing the raw data"
- Compiles to barretenberg proofs (efficient verification)
- Growing ecosystem with JavaScript/Rust bindings
- Can integrate via WASM in browser or CLI

**Key questions to answer:**
- Can Noir represent the signal extraction formulas (entropy, time deltas, ratios) in circuits?
- What's the proving time for a circuit with 8 signal computations?
- Browser proving time via WASM? (Important for client-side generation)
- How hard is the toolchain setup for a Python project?

**Resources:**
- [Noir Docs](https://noir-lang.org/docs)
- [Awesome Noir](https://github.com/noir-lang/awesome-noir)
- Example: [zk-nn](https://github.com/TomAFrench/zk-nn) — neural network inference in Noir

---

### 2. EAS (Ethereum Attestation Service, https://attest.sh)

On-chain attestation registry that might skip custom contract work entirely.

**Why it fits this project:**
- Pre-built smart contracts for registering and verifying attestations
- Schema-based attestations — can define a `GithubFingerprint` schema
- Multi-chain (Ethereum, Polygon, Optimism, Arbitrum, Base)
- Off-chain attestations possible (no gas for attestation creation, only verification)

**Key questions to answer:**
- Can EAS store Ed25519 signatures from Phase 1 as on-chain attestations?
- Schema gas cost vs benefit for the MVP
- Off-chain attestation mode: how does verification work without on-chain data?

**Resources:**
- [EAS Docs](https://docs.attest.sh)
- [EAS SDK](https://github.com/ethereum-attestation-service/eas-sdk)
- [Off-chain attestations](https://docs.attest.sh/docs/developer--tools/off-chain)

---

### 3. Account Abstraction + Wallet Onboarding

For the non-crypto-user signup flow.

**Why it matters:**
- GitHub devs need Magic Link signup (no seed phrases)
- Recruiters need credit card payments (Stripe/MoonPay)
- Both sides need wallets for ZK proof submission/verification

**Key questions to answer:**
- Web3Auth (https://web3auth.io) — social login → non-custodial wallet
- Magic.link (https://magic.link) — email-based wallet generation
- Privy (https://privy.io) — embedded wallets for web2 UX
- Account abstraction (ERC-4337) — gas sponsorship for new users

**Resources:**
- [Web3Auth Docs](https://web3auth.io/docs)
- [ERC-4337](https://eips.ethereum.org/EIPS/eip-4337)
- [Privy Embedded Wallets](https://docs.privy.io)

---

### 4. GitHub Identity Binding

How to provably link a GitHub account to a wallet.

**Options:**
1. **Signed message at auth time** — User signs "I control GitHub @username" with their wallet during signup. Simple, user proves ownership once.
2. **GitHub OAuth + wallet binding** — Service links OAuth identity to wallet address server-side. Less trustless but simpler UX.
3. **ENS/GitHub oracle** — ENS text records or a decentralized oracle maps GitHub → wallet.

---

## Prioritized Research Plan

| Priority | Topic | Decision Needed By |
|----------|-------|-------------------|
| **P0** | Noir circuit feasibility for signal computation | Before Phase 2 implementation |
| **P0** | EAS schema design for attestation format | Before Phase 2 implementation |
| **P1** | Wallet onboarding (Web3Auth vs Magic vs Privy) | Before user signup flow |
| **P2** | GitHub → wallet binding strategy | Before ZK proof submission |
| **P3** | Gas cost analysis for on-chain verification | Before mainnet deployment |

## Recommendation

Start with Noir for the circuit layer + EAS for the attestation registry. Noir handles "prove computation was correct" and EAS handles "publish the proof on-chain". Web3Auth for wallet onboarding. This gives the most leverage with the least custom infrastructure.

A good first Noir prototype: a circuit that proves `response_hash = SHA256(score_payload)` matches a signed attestation, without revealing the payload.
