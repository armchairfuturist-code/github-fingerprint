# S04: Scoring-sp1-core Cross-Comparison Test — UAT

**Milestone:** M002
**Written:** 2026-05-12T09:39:25.585Z

## UAT: Cross-Comparison Zero-Diff Verification

### Preconditions
- Rust toolchain (cargo, rustc) installed
- Workspace cloned at C:\Users\Administrator\Documents\Projects\github-fingerprint

### Test 1: Single fixture comparison (sample_profile)
1. Run `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/sample_profile.json`
2. **Expected:** Output shows PASS for all 12 signals, overall_score, risk_flags, signals_below_threshold
3. **Expected:** Exit code 0

### Test 2: All fixtures comparison
1. Run `cargo run -p scoring-cross-compare -- --all-fixtures`
2. **Expected:** Each fixture reports ALL PASS before proceeding to next
3. **Expected:** Final message "All fixtures match perfectly (exit 0)"
4. **Expected:** Exit code 0

### Test 3: No regression in Rust test suite
1. Run `cargo test`
2. **Expected:** All 8 crates pass, 0 failures

### Test 4: No regression in Python test suite
1. Run `py -m pytest`
2. **Expected:** 286 tests pass, 0 failures, 0 errors

### Edge Cases
- **Empty input:** `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/empty_input.json` exits 0 with ALL PASS
- **Minimal profile:** `cargo run -p scoring-cross-compare -- --fixture py-scoring-ref/fixtures/minimal_profile.json` exits 0 with ALL PASS

### UAT Type
Automated regression + integration verification

### Not Proven By This UAT
- Does not test that SP1 zkVM can prove the scoring function (covered by S02)
- Does not test the async proving queue or proof status endpoint (covered by S03)
- Does not test on-chain Solidity verifier contract (covered by S05)
