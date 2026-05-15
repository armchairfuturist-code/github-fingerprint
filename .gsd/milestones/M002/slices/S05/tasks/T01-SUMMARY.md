---
id: T01
parent: S05
milestone: M002
key_files:
  - Cargo.toml
  - .github/workflows/ci.yml
  - contracts/package.json
  - contracts/package-lock.json
key_decisions:
  - Created contracts/package.json with ethers dependency so the contract test stage can run npm ci — without this, the CI workflow would fail on the contract test job
duration: 
verification_result: passed
completed_at: 2026-05-12T09:50:29.285Z
blocker_discovered: false
---

# T01: Added 3 SP1-related workspace members to Cargo.toml (scoring-sp1/program, scoring-sp1/script, scoring-prover-cli) and created a 3-stage GitHub Actions CI workflow (Rust SP1 build & test, Python tests, contract tests)

**Added 3 SP1-related workspace members to Cargo.toml (scoring-sp1/program, scoring-sp1/script, scoring-prover-cli) and created a 3-stage GitHub Actions CI workflow (Rust SP1 build & test, Python tests, contract tests)**

## What Happened

Task T01 accomplished two things. First, it added the three missing workspace members to the root Cargo.toml — scoring-sp1/program (SP1 guest program), scoring-sp1/script (SP1 host script), and scoring-prover-cli (subprocess bridge). These crates existed with their own Cargo.toml files but were not registered as workspace members, meaning they wouldn't be built or tested in CI. Second, it created .github/workflows/ci.yml with three independent job stages running on ubuntu-latest: (1) Core Rust — installs Rust 1.91.0 via setup-rust-toolchain, installs the SP1 toolchain via sp1up (using secrets.GH_PAT for rate limiting), caches ~/.cargo and ~/.sp1/circuits, runs cargo prove build on the SP1 guest program, then cargo build --workspace and cargo test --workspace; (2) Python — sets up Python 3.12, installs deps from requirements.txt with pip caching, runs python -m pytest -x --tb=short; (3) Contract — sets up Node.js 20, runs npm ci in contracts/ (for which contracts/package.json and contracts/package-lock.json were also created since they didn't exist), then runs node tests/test_verifier_contract.cjs.

## Verification

Verified via grep all must-haves: (1) grep -q "scoring-sp1/program" Cargo.toml passes, (2) grep -q "scoring-sp1/script" Cargo.toml passes, (3) grep -q "scoring-prover-cli" Cargo.toml passes, (4) grep -q "cargo prove build" .github/workflows/ci.yml passes, (5) grep -q "pytest" .github/workflows/ci.yml passes, (6) grep -q "node tests/test_verifier_contract.cjs" .github/workflows/ci.yml passes, (7) grep -q "sp1/circuits" .github/workflows/ci.yml confirms SP1 caching is present.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -q "scoring-sp1/program" Cargo.toml && echo pass` | 0 | ✅ pass | 50ms |
| 2 | `grep -q "scoring-sp1/script" Cargo.toml && echo pass` | 0 | ✅ pass | 50ms |
| 3 | `grep -q "scoring-prover-cli" Cargo.toml && echo pass` | 0 | ✅ pass | 50ms |
| 4 | `grep -q "cargo prove build" .github/workflows/ci.yml && echo pass` | 0 | ✅ pass | 50ms |
| 5 | `grep -q "pytest" .github/workflows/ci.yml && echo pass` | 0 | ✅ pass | 50ms |
| 6 | `grep -q "node tests/test_verifier_contract.cjs" .github/workflows/ci.yml && echo pass` | 0 | ✅ pass | 50ms |
| 7 | `grep -q "sp1/circuits" .github/workflows/ci.yml && echo pass` | 0 | ✅ pass | 50ms |

## Deviations

Created contracts/package.json and contracts/package-lock.json as supporting files for the Contract Tests CI stage — these didn't exist and are required for `npm ci` to work. The task plan didn't explicitly mention creating these but they're necessary for the CI workflow to function.

## Known Issues

The package-lock.json will need regeneration if contracts/package.json dependencies change. The CI workflow's Rust stage uses RUSTFLAGS: -D warnings at both the env and job level — the job-level override is intentional because the CI job explicitly sets it, but the env-level setting is redundant for other jobs.

## Files Created/Modified

- `Cargo.toml`
- `.github/workflows/ci.yml`
- `contracts/package.json`
- `contracts/package-lock.json`
