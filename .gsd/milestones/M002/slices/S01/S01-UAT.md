# S01: Rust Scoring Library — UAT

**Milestone:** M002
**Written:** 2026-05-12T07:56:51.839Z

## S01 UAT: Rust Scoring Library

### Verification Checklist

| Check | Criteria | Result |
|---|---|---|
| Project compiles | `cargo build` exits 0 | ✅ |
| All tests pass | `cargo test` — 8 unit tests pass | ✅ |
| Python comparison | Zero diffs on sample_profile.json | ✅ |
| CLI works | Reads JSON, outputs ScoreOutput | ✅ |
| Profile weights | Sum to ~1.0 for all 3 profiles | ✅ |
| Cycle count estimate | < 1M cycles, ~200K typical | ✅ |
| Empty inputs handled | Empty repos/commits → score 0 | ✅ |

### Commands
```bash
cargo test --lib -p scoring-core
cargo build
./target/debug/scoring-cli.exe --input py-scoring-ref/fixtures/sample_profile.json
cd py-scoring-ref && python compare.py
```
