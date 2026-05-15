---
phase: M002
phase_name: ZK Proving Layer
project: github-fingerprint
generated: 2026-05-12T10:30:00.000Z
counts:
  decisions: 5
  lessons: 4
  patterns: 4
  surprises: 1
missing_artifacts: []
---

# M002: ZK Proving Layer — Structured Learnings

## Decisions

### D001 — Separated scoring-sp1-core as an independent no_std crate
Instead of attempting to make scoring-core compile to both std (Windows CLIs and Python bindings) and no_std (RISC-V SP1 guest), we created scoring-sp1-core as a separate crate with its own no_std-compatible date parser, signal extraction, and scoring engine. This preserves ergonomic Rust std features (chrono, std::collections) in the development path while keeping the RISC-V binary small and dependency-free.
Source: S02-SUMMARY/Key Decisions

### D002 — Celery over FastAPI BackgroundTasks for async proof queue
Despite FastAPI's built-in BackgroundTasks being lighter-weight, the need for at-least-once delivery semantics (acks_late + reject_on_worker_lost), configurable retries with exponential backoff and jitter, and a dedicated worker separate from the API process drove the choice of Celery with Redis.
Source: S03-SUMMARY/Key Decisions

### D003 — In-memory ProofStatusStore with Redis upgrade path
Rather than requiring Redis for proof status tracking (which would add a hard infrastructure dependency for the status endpoint itself), we built a thread-safe in-memory ProofStatusStore with a singleton accessor pattern. This keeps the GET /proof/{username}/status endpoint operational even without Redis, while the module-level get_store() interface enables a future swap to Redis-persisted storage without changing consumers.
Source: S03-SUMMARY/Key Decisions

### D004 — VKey registry pattern for multi-program support
The SP1Verifier contract uses a registry mapping (programVKey → verified boolean) rather than storing a single program VKey. This enables support for multiple scoring program versions or different proof programs without redeploying the verifier contract — the deployer registers additional VKeys.
Source: S03-SUMMARY/Key Decisions

### D005 — Cross-comparison crate for ZK-engine fidelity
Created scoring-cross-compare as a standalone Rust binary that feeds identical ScoreInput fixtures to both scoring-core (std, reference) and scoring-sp1-core (no_std, SP1), comparing all 12 signals with exact f64 equality. This provides an automated CI gate to detect when the SP1 engine diverges from the reference engine, preventing silent trust breaks in the ZK proof chain.
Source: S04-SUMMARY/Key Decisions

## Lessons

### L001 — SP1 toolchain is not available on Windows
The `cargo prove build` command (part of the `sp1up` toolchain installer) does not support Windows due to dependency on Unix-specific binaries (unzip, POSIX shell scripts). This means all SP1 compilation, proof generation, and proof verification must happen on Linux or macOS. Mitigation: CI pipeline on ubuntu-latest is configured with sp1up + SP1 circuit caching. Local development on Windows stops at cargo build -p scoring-sp1-core (which compiles to host target, not RISC-V).
Source: S01-SUMMARY/Deviations, S02-SUMMARY/Deviations

### L002 — solc 0.8.28 viaIR is required to avoid stack-too-deep with BN254 pairing
The SP1 Groth16 verifier contract includes heavy inline Yul assembly for BN254 elliptic curve pairings (ECADD, ECMUL, ECPAIRING precompiles). The Solidity compiler's default pipeline hits stack-too-deep errors due to register pressure from the pairing expression. Using `solc --via-ir` (the Yul intermediate representation pipeline) resolves this by optimizing the expression before code generation.
Source: S03-SUMMARY/Key Decisions

### L003 — Python subprocess wrapper must handle missing binary gracefully
The prover client wrapper (api/prover_client.py) calls the scoring-prover-cli binary via subprocess. When the binary doesn't exist (common during development before a Linux build), the wrapper catches FileNotFoundError and returns structured error metadata with status "binary-not-found" rather than crashing the API process. This pattern is essential for graceful degradation when the SP1 toolchain isn't available.
Source: S02-UAT/Edge Cases

### L004 — Pytest must be invoked as `py -m pytest` not bare `pytest`
On Windows, the bare `pytest` command may invoke a Windows Store stub rather than the installed pip package, returning exit code 2 with a confusing error. The project root is also not on sys.path, so module imports fail when running pytest directly. Using `py -m pytest` resolves both issues. A root-level conftest.py would fix the sys.path issue permanently but is a pre-existing project gap.
Source: S04-SUMMARY/Known Limitations

## Patterns

### P001 — Task-level VERIFY.json pattern for verification evidence
All 21 tasks in M002 include a T0N-VERIFY.json file that records the exact verification command, exit code, verdict, and duration. This creates a machine-readable audit trail for each task completion that survives context compaction and can be queried via gsd_exec_search.
Source: S01-SUMMARY, S02-SUMMARY, S03-SUMMARY, S04-SUMMARY, S05-SUMMARY

### P002 — Three-crate Rust workspace (types/core/CLI)
The Rust scoring library is organized as three crates in a workspace: scoring-types (shared data types), scoring-core (engine + profiles), and scoring-cli (binary interface). This separation allows scoring-core to be reused by scoring-sp1-core without pulling in CLI dependencies, and enables independent testing of each layer.
Source: S01-SUMMARY/Patterns Established

### P003 — auto-mocking conftest fixture for Redis-optional testing
The tests/conftest.py fixture auto-mocks enqueue_proof to prevent test hangs when Redis is unavailable. This pattern uses a conftest hook that patches the enqueue function at module import time, so no test needs to opt in — the mock is always active unless explicitly overridden. This keeps the test suite fast and environment-independent.
Source: S03-SUMMARY/Patterns Established

### P004 — Deterministic wallet from typed seed for reproducible deployment
The contract deployment pipeline generates a deterministic wallet from a fixed hexadecimal seed (SHA-256 of a typed string "GithubFingerprintSP1VerifierDeployer"), ensuring the same deployer address across environments. This enables idempotent deployment checks and reproducible CI builds.
Source: S03-SUMMARY/Patterns Established

## Surprises

### S001 — Windows host cannot run SP1 toolchain at all
The SP1 toolchain installer (sp1up) has no Windows support — not just limited, but completely absent. This is a fundamental constraint that wasn't anticipated during planning. All SP1-related work (compilation, proof generation, proof verification) requires Linux or macOS. The CI pipeline on ubuntu-latest is the only viable build path. This affected S01 (analytical cycle count estimates instead of measured), S02 (no cargo prove build on this host), S05 (CI workflow designed for Linux-only execution), and the overall verification strategy (many checks deferred to CI).
Source: S01-SUMMARY/Deviations, S02-SUMMARY/Deviations, S05-SUMMARY
