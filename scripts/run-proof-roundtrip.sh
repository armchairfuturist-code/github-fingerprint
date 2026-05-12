#!/usr/bin/env bash
# scripts/run-proof-roundtrip.sh — E2E proof round-trip orchestration script.
#
# Chains the full pipeline: ELF build → proof generation → on-chain submission → verification.
# Supports dry-run mode for CI/preview.
#
# Usage: ./scripts/run-proof-roundtrip.sh [options]
#
# Options:
#   --fixture <path>         ScoreInput fixture (default: scoring-sp1/fixtures/sample_profile.json)
#   --elf-path <path>        ELF path (default: scoring-sp1/program/elf/riscv32im-succinct-zkvm-elf)
#   --prover-mode <local|network>  SP1 prover mode (default: local)
#   --rpc-url <url>          Base Sepolia RPC (default: https://sepolia.base.org)
#   --contract <address>     SP1Verifier contract address
#   --dry-run                Print planned steps without executing
#   --clean                  Delete stale ELF and proof before starting
#   --help                   Show usage

set -euo pipefail

# ── Constants & Defaults ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DEFAULT_FIXTURE="$REPO_ROOT/scoring-sp1/fixtures/sample_profile.json"
DEFAULT_ELF_PATH="$REPO_ROOT/scoring-sp1/program/elf/riscv32im-succinct-zkvm-elf"
DEFAULT_PROVER_MODE="local"
DEFAULT_RPC_URL="https://sepolia.base.org"

PROOF_OUTPUT="proof.bin"
TOTAL_STEPS=9

TEMP_FILES=()

# ── Help ───────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $(basename "$0") [options]

Chains ELF build → proof generation → on-chain submission → verification.

Options:
  --fixture <path>         ScoreInput fixture (default: scoring-sp1/fixtures/sample_profile.json)
  --elf-path <path>        ELF path (default: scoring-sp1/program/elf/riscv32im-succinct-zkvm-elf)
  --prover-mode <local|network>  SP1 prover mode (default: local)
  --rpc-url <url>          Base Sepolia RPC (default: https://sepolia.base.org)
  --contract <address>     SP1Verifier contract address
  --dry-run                Print planned steps without executing
  --clean                  Delete stale ELF and proof before starting
  --help                   Show this usage message

Environment:
  PRIVATE_KEY              Required for on-chain submission
  SP1_VKEY                 Program verification key (bytes32 hex)

Examples:
  # Dry-run to check prerequisites
  $(basename "$0") --dry-run

  # Full round-trip with default fixture
  PRIVATE_KEY=0x... $(basename "$0")

  # Clean rebuild with custom fixture
  PRIVATE_KEY=0x... $(basename "$0") --clean --fixture /path/to/input.json

  # Using Succinct network prover
  SP1_PROVER_KEY=0x... PRIVATE_KEY=0x... $(basename "$0") --prover-mode network
EOF
    exit 0
}

# ── Parse CLI Args ─────────────────────────────────────────────────────
FIXTURE=""
ELF_PATH=""
PROVER_MODE=""
RPC_URL=""
CONTRACT_ADDR=""
DRY_RUN=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fixture)     FIXTURE="$2"; shift 2 ;;
        --elf-path)    ELF_PATH="$2"; shift 2 ;;
        --prover-mode) PROVER_MODE="$2"; shift 2 ;;
        --rpc-url)     RPC_URL="$2"; shift 2 ;;
        --contract)    CONTRACT_ADDR="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=true; shift ;;
        --clean)       CLEAN=true; shift ;;
        --help)        usage ;;
        *)
            echo "❌ Unknown option: $1"
            usage
            ;;
    esac
done

# Apply defaults
FIXTURE="${FIXTURE:-$DEFAULT_FIXTURE}"
ELF_PATH="${ELF_PATH:-$DEFAULT_ELF_PATH}"
PROVER_MODE="${PROVER_MODE:-$DEFAULT_PROVER_MODE}"
RPC_URL="${RPC_URL:-$DEFAULT_RPC_URL}"
export SP1_PROVER="$PROVER_MODE"

# ── Cleanup Handler ────────────────────────────────────────────────────
cleanup() {
    local ec=$?
    for f in "${TEMP_FILES[@]}"; do
        [[ -f "$f" ]] && rm -f "$f"
    done
    exit "$ec"
}
trap cleanup EXIT

# ── Utility Functions ──────────────────────────────────────────────────

step_header() {
    local sn="$1" nm="$2"
    printf "\n[%s/%s] → %s...\n" "$sn" "$TOTAL_STEPS" "$nm"
}

step_ok() {
    local sn="$1" nm="$2" dur="$3"
    printf "[%s/%s] ✔ %s (duration: %ss)\n" "$sn" "$TOTAL_STEPS" "$nm" "$dur"
}

step_fail() {
    local sn="$1" nm="$2" err="$3" ec="$4"
    printf "[%s/%s] ✗ %s (error: %s)\n" "$sn" "$TOTAL_STEPS" "$nm" "$err"
    exit "$ec"
}

check_prereq() {
    command -v "$1" &>/dev/null
}

get_file_size() {
    local f="$1"
    stat -c '%s' "$f" 2>/dev/null || stat -f '%z' "$f" 2>/dev/null || echo "?"
}

get_file_mtime() {
    local f="$1"
    stat -c '%Y' "$f" 2>/dev/null || stat -f '%m' "$f" 2>/dev/null || echo "0"
}

# ═══════════════════════════════════════════════════════════════════════
#  DRY-RUN MODE
# ═══════════════════════════════════════════════════════════════════════

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  DRY RUN — Proof Round-Trip Plan"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "  Project root:    $REPO_ROOT"
    echo "  Fixture:         $FIXTURE"
    echo "  ELF path:        $ELF_PATH"
    echo "  Prover mode:     $PROVER_MODE"
    echo "  RPC URL:         $RPC_URL"
    echo "  Contract:        ${CONTRACT_ADDR:-<from deployed-address.txt>}"
    echo "  Clean:           $CLEAN"
    echo ""

    # Check prerequisites
    echo "  Prerequisites:"
    for pair in "cargo:cargo" "cargo-prove:cargo-prove" "sp1up:sp1up" "node:node" "docker:docker" "openssl:openssl"; do
        cmd="${pair%%:*}"
        label="${pair##*:}"
        if check_prereq "$cmd"; then
            echo "    ${label}:          ✓ found"
        else
            case "$cmd" in
                docker) echo "    ${label}:          ⚠ not found (CPU proving may timeout)" ;;
                sp1up)  echo "    ${label}:          ⚠ not found (may still be available via cargo-prove)" ;;
                *)      echo "    ${label}:          ✗ NOT FOUND" ;;
            esac
        fi
    done

    # Check ELF staleness
    echo ""
    echo "  ELF status:"
    if [[ -f "$ELF_PATH" ]]; then
        elf_mtime=$(get_file_mtime "$ELF_PATH")
        now=$(date +%s)
        age=$(( now - elf_mtime ))
        echo "    ELF exists, age: ${age}s"
        echo "    Clean rebuild:   $CLEAN"
    else
        echo "    ELF does not exist (will be built)"
    fi
    echo ""

    # Print planned steps
    echo "  Planned steps:"
    echo ""
    echo "    Step 1/9:  Check prerequisites"
    echo "               which cargo, which cargo-prove, which node"
    echo ""
    echo "    Step 2/9:  Clean stale artifacts (if --clean)"
    echo "               rm -f $ELF_PATH $PROOF_OUTPUT"
    echo ""
    echo "    Step 3/9:  Build SP1 guest ELF"
    echo "               cd scoring-sp1/program && cargo prove build"
    echo ""
    echo "    Step 4/9:  Verify ELF exists"
    echo "               Check: $ELF_PATH"
    echo ""
    echo "    Step 5/9:  Build SP1 host script (release)"
    echo "               cargo build -p scoring-sp1-script --release"
    echo ""
    echo "    Step 6/9:  Generate proof"
    echo "               cargo run -p scoring-sp1-script --release -- --input $FIXTURE"
    echo "               Output: $PROOF_OUTPUT"
    echo ""
    echo "    Step 7/9:  Verify proof was generated"
    echo "               Check: $PROOF_OUTPUT"
    echo ""
    echo "    Step 8/9:  Submit proof on-chain"
    echo "               node contracts/submit-proof.cjs --proof $PROOF_OUTPUT"
    echo "               --rpc-url $RPC_URL ${CONTRACT_ADDR:+--contract $CONTRACT_ADDR}"
    echo ""
    echo "    Step 9/9:  Print summary"
    echo "               ELF size, proof size, verification result"
    echo ""

    # Estimated durations
    echo "  Estimated durations (local CPU proving):"
    echo "    Step 3 (ELF build):     ~30-120s (first build, cached after)"
    echo "    Step 5 (build script):  ~30-90s"
    echo "    Step 6 (prove):         ~5-30min (depends on program complexity)"
    echo "    Step 8 (submit):        ~5-15s"
    echo ""

    # Check fixture
    if [[ -f "$FIXTURE" ]]; then
        echo "  Fixture:         ✓ $FIXTURE"
    else
        echo "  Fixture:         ⚠ NOT FOUND at $FIXTURE"
        echo "                   (provide --fixture <path> to an existing file)"
    fi

    echo ""
    echo "─────────────────────────────────────────────────────────"
    echo "  ✅ Dry-run complete. Remove --dry-run to execute."
    echo "═══════════════════════════════════════════════════════════"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════
#  EXECUTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Proof Round-Trip Pipeline"
echo "═══════════════════════════════════════════════════════════"
echo "  Started at:    $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  Fixture:       $FIXTURE"
echo "  Prover mode:   $PROVER_MODE"
echo "  RPC URL:       $RPC_URL"
echo ""

# ── Step 1: Check Prerequisites ──────────────────────────────────────
step_header 1 "Check prerequisites"

PREREQ_FAILED=false

check_prereq cargo       || { echo "  ✗ cargo: NOT FOUND — install Rust toolchain"; PREREQ_FAILED=true; }
check_prereq cargo-prove || { echo "  ✗ cargo-prove: NOT FOUND — run 'sp1up' or install SP1 toolchain"; PREREQ_FAILED=true; }
check_prereq sp1up       || { echo "  ⚠ sp1up: NOT FOUND in PATH (may still be available via cargo-prove)"; }
check_prereq node        || { echo "  ✗ node: NOT FOUND — install Node.js"; PREREQ_FAILED=true; }
check_prereq openssl     || { echo "  ⚠ openssl: NOT FOUND — may be needed for SP1 key generation"; }
check_prereq docker      || { echo "  ⚠ docker: NOT FOUND — groth16 proving will use CPU (may timeout)"; }

if [[ "$PREREQ_FAILED" == true ]]; then
    step_fail 1 "Check prerequisites" "Missing required tools (see above)" 1
fi
step_ok 1 "Check prerequisites" 0

# ── Step 2: Clean stale artifacts (if --clean) ──────────────────────
if [[ "$CLEAN" == true ]]; then
    step_header 2 "Clean stale artifacts"
    any_cleaned=false

    if [[ -f "$ELF_PATH" ]]; then
        rm -f "$ELF_PATH"
        echo "  Removed ELF: $ELF_PATH"
        any_cleaned=true
    fi
    if [[ -f "$PROOF_OUTPUT" ]]; then
        rm -f "$PROOF_OUTPUT"
        echo "  Removed proof: $PROOF_OUTPUT"
        any_cleaned=true
    fi
    if [[ "$any_cleaned" == false ]]; then
        echo "  Nothing to clean."
    fi
    step_ok 2 "Clean stale artifacts" 0
else
    echo ""
    echo "[2/9] → Clean stale artifacts..."
    echo "[2/9] ✔ Clean stale artifacts (--clean not set, skipped)"
fi

# ── Step 3: Build SP1 guest ELF ─────────────────────────────────────
(
    step_header 3 "Build SP1 guest ELF"
    cd "$REPO_ROOT/scoring-sp1/program"
    start_time=$(date +%s)
    if cargo prove build; then
        end_time=$(date +%s)
        step_ok 3 "Build SP1 guest ELF" "$(( end_time - start_time ))"
    else
        ec=$?
        step_fail 3 "Build SP1 guest ELF" "cargo prove build failed (exit code $ec)" "$ec"
    fi
)

# ── Step 4: Verify ELF exists ───────────────────────────────────────
step_header 4 "Verify ELF exists"

if [[ -f "$ELF_PATH" ]]; then
    elf_size=$(get_file_size "$ELF_PATH")
    echo "  ELF found: $ELF_PATH ($elf_size bytes)"
    step_ok 4 "Verify ELF exists" 0
else
    step_fail 4 "Verify ELF exists" "ELF not found at $ELF_PATH" 1
fi

# ── Step 5: Build SP1 host script ───────────────────────────────────
(
    step_header 5 "Build SP1 host script (release)"
    cd "$REPO_ROOT"
    start_time=$(date +%s)
    if cargo build -p scoring-sp1-script --release; then
        end_time=$(date +%s)
        step_ok 5 "Build SP1 host script (release)" "$(( end_time - start_time ))"
    else
        ec=$?
        step_fail 5 "Build SP1 host script (release)" "cargo build failed (exit code $ec)" "$ec"
    fi
)

# ── Step 6: Generate proof ─────────────────────────────────────────
(
    step_header 6 "Generate proof"
    cd "$REPO_ROOT"

    export SP1_ELF_PATH="$ELF_PATH"
    export SP1_PROOF_OUTPUT="$REPO_ROOT/$PROOF_OUTPUT"

    echo "  ELF path:      $SP1_ELF_PATH"
    echo "  Proof output:  $SP1_PROOF_OUTPUT"
    echo "  Fixture:       $FIXTURE"
    echo "  Prover mode:   $SP1_PROVER"

    start_time=$(date +%s)
    if cargo run -p scoring-sp1-script --release -- --input "$FIXTURE"; then
        end_time=$(date +%s)
        step_ok 6 "Generate proof" "$(( end_time - start_time ))"
    else
        ec=$?
        step_fail 6 "Generate proof" "Proof generation failed (exit code $ec)" "$ec"
    fi
)

# ── Step 7: Verify proof was generated ─────────────────────────────
step_header 7 "Verify proof was generated"

proof_path="$REPO_ROOT/$PROOF_OUTPUT"
if [[ -f "$proof_path" ]]; then
    proof_size=$(get_file_size "$proof_path")
    echo "  Proof found: $proof_path ($proof_size bytes)"
    step_ok 7 "Verify proof was generated" 0
else
    step_fail 7 "Verify proof was generated" "Proof not found at $proof_path" 1
fi

# ── Step 8: Submit proof on-chain ───────────────────────────────────
step_header 8 "Submit proof on-chain"

submit_args=()
submit_args+=(--proof "$proof_path")
submit_args+=(--rpc-url "$RPC_URL")
if [[ -n "$CONTRACT_ADDR" ]]; then
    submit_args+=(--contract "$CONTRACT_ADDR")
fi

echo "  Running: node contracts/submit-proof.cjs ${submit_args[*]}"

start_time=$(date +%s)
if node "$REPO_ROOT/contracts/submit-proof.cjs" "${submit_args[@]}"; then
    end_time=$(date +%s)
    step_ok 8 "Submit proof on-chain" "$(( end_time - start_time ))"
else
    ec=$?
    step_fail 8 "Submit proof on-chain" "On-chain submission failed (exit code $ec)" "$ec"
fi

# ── Step 9: Print summary ──────────────────────────────────────────
step_header 9 "Print summary"

elf_size=$(get_file_size "$ELF_PATH")
proof_size=$(get_file_size "$proof_path")

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Pipeline Complete"
echo "═══════════════════════════════════════════════════════════"
echo "  Completed at:  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  ELF size:      $elf_size bytes"
echo "  Proof size:    $proof_size bytes"
echo "  Fixture:       $FIXTURE"
echo "  Prover mode:   $PROVER_MODE"
echo "  RPC URL:       $RPC_URL"
echo "  Contract:      ${CONTRACT_ADDR:-<from deployed-address.txt>}"
echo ""

step_ok 9 "Print summary" 0

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Round-trip completed successfully"
echo "═══════════════════════════════════════════════════════════"
