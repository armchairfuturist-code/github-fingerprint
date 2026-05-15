# Codebase Map

Generated: 2026-05-15T05:50:03Z | Files: 99 | Described: 0/99
<!-- gsd:codebase-meta {"generatedAt":"2026-05-15T05:50:03Z","fingerprint":"bc91adb49cbf65c6bd621b8de037cf65b9783fbf","fileCount":99,"truncated":false} -->

### (root)/
- `.env.example`
- `.gitignore`
- `AGENTS.md`
- `Cargo.toml`
- `index.html`
- `README.md`
- `requirements.txt`
- `skills-lock.json`
- `smoke_test.py`
- `test_fingerprint.py`

### .github/workflows/
- `.github/workflows/ci.yml`

### .keys/
- `.keys/attestation_private.pem`
- `.keys/attestation_public.pem`

### .qwen/
- `.qwen/QWEN.md`

### .test-tmp/
- `.test-tmp/test-proof.bin`

### api/
- `api/__init__.py`
- `api/celery_app.py`
- `api/main.py`
- `api/proof_status.py`
- `api/proof_tasks.py`
- `api/prover_client.py`
- `api/worker.py`

### attest/
- `attest/__init__.py`
- `attest/config.py`
- `attest/signer.py`

### attestation/
- `attestation/__init__.py`
- `attestation/signer.py`

### contracts/
- `contracts/deploy-wallet.json`
- `contracts/deploy.cjs`
- `contracts/deployed-address.txt`
- `contracts/ISP1Verifier.sol`
- `contracts/package-lock.json`
- `contracts/package.json`
- `contracts/setup-wallet.cjs`
- `contracts/SP1Verifier.sol`
- `contracts/submit-proof.cjs`

### contracts/abi/
- `contracts/abi/SP1Verifier.json`

### crawler/
- `crawler/github_api.py`

### docs/
- `docs/cycle-count-report.md`
- `docs/failure-modes.md`
- `docs/personality-model.md`
- `docs/zk-research-log.md`

### docs/plans/
- `docs/plans/sprint-001.md`

### py-scoring-ref/
- `py-scoring-ref/compare.py`

### py-scoring-ref/fixtures/
- `py-scoring-ref/fixtures/empty_input.json`
- `py-scoring-ref/fixtures/minimal_profile.json`
- `py-scoring-ref/fixtures/sample_profile.json`

### scoring/
- `scoring/__init__.py`
- `scoring/engine.py`
- `scoring/profiles.py`

### scoring-cli/
- `scoring-cli/Cargo.toml`

### scoring-cli/src/
- `scoring-cli/src/main.rs`

### scoring-core/
- `scoring-core/Cargo.toml`

### scoring-core/src/
- `scoring-core/src/engine.rs`
- `scoring-core/src/lib.rs`
- `scoring-core/src/profiles.rs`

### scoring-cross-compare/
- `scoring-cross-compare/Cargo.toml`

### scoring-cross-compare/src/
- `scoring-cross-compare/src/main.rs`

### scoring-prover-cli/
- `scoring-prover-cli/Cargo.toml`

### scoring-prover-cli/src/
- `scoring-prover-cli/src/main.rs`

### scoring-sp1-core/
- `scoring-sp1-core/Cargo.toml`

### scoring-sp1-core/src/
- `scoring-sp1-core/src/date_parser.rs`
- `scoring-sp1-core/src/engine.rs`
- `scoring-sp1-core/src/lib.rs`
- `scoring-sp1-core/src/profiles.rs`

### scoring-sp1/program/
- `scoring-sp1/program/Cargo.toml`

### scoring-sp1/program/src/
- `scoring-sp1/program/src/main.rs`

### scoring-sp1/script/
- `scoring-sp1/script/Cargo.toml`

### scoring-sp1/script/src/
- `scoring-sp1/script/src/main.rs`

### scoring-types/
- `scoring-types/Cargo.toml`

### scoring-types/src/
- `scoring-types/src/lib.rs`

### scripts/
- `scripts/run-proof-roundtrip.sh`

### signals/
- `signals/extractor.py`
- `signals/personality.py`

### static/
- `static/index.html`

### static/css/
- `static/css/style.css`

### templates/
- `templates/404.html`
- `templates/profile.html`

### tests/
- `tests/conftest.py`
- `tests/test_api.py`
- `tests/test_attest.py`
- `tests/test_attestation.py`
- `tests/test_celery.py`
- `tests/test_crawler.py`
- `tests/test_integration.py`
- `tests/test_optin.py`
- `tests/test_personality.py`
- `tests/test_profile_template.py`
- `tests/test_profile.py`
- `tests/test_proof_status.py`
- `tests/test_proof_tasks.py`
- `tests/test_prover_client.py`
- `tests/test_proving_e2e.py`
- `tests/test_scoring.py`
- `tests/test_verifier_contract.cjs`
- `tests/test_wallet.py`

### wallet/
- `wallet/__init__.py`
- `wallet/provider.py`
- `wallet/store.py`
