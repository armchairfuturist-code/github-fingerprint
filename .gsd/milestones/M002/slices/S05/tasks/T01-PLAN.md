---
estimated_steps: 33
estimated_files: 2
skills_used: []
---

# T01: Add missing crates to workspace and create GitHub Actions CI workflow

## Why
scoring-sp1/program (guest), scoring-sp1/script (host), and scoring-prover-cli (subprocess bridge) are not workspace members — they won't build in CI. The SP1 guest program has never been built outside a local dev machine; `cargo prove build` on Linux CI is the highest-risk step for this milestone.

## Files
- `Cargo.toml` — add 3 workspace members
- `.github/workflows/ci.yml` — new CI workflow

## Do
1. **Add to workspace members** in root `Cargo.toml`:
   - `"scoring-sp1/program"`
   - `"scoring-sp1/script"`
   - `"scoring-prover-cli"`

2. **Create `.github/workflows/ci.yml`** with three job stages:

   **Stage 1 — Core Rust Build & Test** (`ubuntu-latest`):
   - Install Rust 1.91.0 via `actions-rust-lang/setup-rust-toolchain@v1`
   - Install SP1 toolchain: `curl -L https://sp1up.succinct.xyz | bash && ~/.sp1/bin/sp1up`
   - Add `~/.sp1/bin` to PATH
   - Cache `~/.cargo` and `~/.sp1/circuits` with `actions/cache@v3` — key based on hash of `Cargo.lock` + SP1 version
   - `cargo prove build` in `scoring-sp1/program/`
   - `cargo build --workspace`
   - `cargo test --workspace`

   **Stage 2 — Python Tests** (`ubuntu-latest`):
   - Setup Python 3.12, install deps from `requirements.txt`
   - `pip install -e .` (if setup.py exists) or `pip install -r requirements.txt`
   - `python -m pytest tests/ -x --tb=short`

   **Stage 3 — Contract Tests** (`ubuntu-latest`):
   - Setup Node 20, `npm ci` in `contracts/`
   - `node tests/test_verifier_contract.cjs`

3. **Use `secrets.GH_PAT`** for `sp1up` to avoid GitHub API rate limiting

## Must-haves
- All 3 workspace members added to `Cargo.toml` members array
- CI workflow runs `cargo prove build` in `scoring-sp1/program/`
- CI workflow has caching for `~/.cargo` and `~/.sp1/circuits`
- Python test stage exists and uses `python -m pytest`
- Contract test stage exists

## Inputs

- `Cargo.toml`
- `scoring-sp1/program/Cargo.toml`
- `scoring-sp1/script/Cargo.toml`
- `scoring-prover-cli/Cargo.toml`
- `requirements.txt`
- `tests/test_verifier_contract.cjs`

## Expected Output

- `Cargo.toml`
- `.github/workflows/ci.yml`

## Verification

grep -q "scoring-sp1/program" Cargo.toml && grep -q "cargo prove build" .github/workflows/ci.yml && grep -q "pytest" .github/workflows/ci.yml
