#!/usr/bin/env node
/**
 * submit-proof.cjs — Submit a Groth16 proof to the SP1Verifier contract on Base Sepolia.
 *
 * Reads a bincode-serialized SP1ProofWithVKey from disk and calls verifyProof
 * on the deployed SP1Verifier contract. Supports dry-run mode for CI/preview.
 *
 * Usage:
 *   node contracts/submit-proof.cjs [options]
 *
 * Options:
 *   --proof <path>        Path to proof.bin (default: proof.bin)
 *   --rpc-url <url>       Base Sepolia RPC (default: https://sepolia.base.org)
 *   --contract <address>  SP1Verifier contract address (reads from deployed-address.txt if omitted)
 *   --vkey <hex>          Program verification key hex (bytes32). Overrides auto-extraction from proof.
 *   --public-inputs <hex> Hex-encoded public values (optional, overrides auto-extraction)
 *   --dry-run             Print plan without sending transaction
 *   --help                Show this usage message
 *
 * Environment:
 *   SP1_VKEY              Alternative way to provide the program verification key
 *   PRIVATE_KEY           Required: deployer wallet private key
 *
 * Exit codes:
 *   0 — proof verified successfully
 *   1 — error (missing file, RPC failure, proof rejected, etc.)
 */

const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

// ── Constants ─────────────────────────────────────────────────────────
const DEFAULT_RPC_URL = 'https://sepolia.base.org';
const CHAIN_ID = 84532;
const SCRIPT_DIR = __dirname;

// ── CLI Parsing ───────────────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    printUsage();
    process.exit(0);
  }

  const opts = {
    proof: 'proof.bin',
    rpcUrl: DEFAULT_RPC_URL,
    contract: null,
    vkey: null,
    publicInputs: null,
    dryRun: false,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--proof':
        opts.proof = args[++i];
        break;
      case '--rpc-url':
        opts.rpcUrl = args[++i];
        break;
      case '--contract':
        opts.contract = args[++i];
        break;
      case '--vkey':
        opts.vkey = args[++i];
        break;
      case '--public-inputs':
        opts.publicInputs = args[++i];
        break;
      case '--dry-run':
        opts.dryRun = true;
        break;
      default:
        console.error(`❌ Unknown option: ${args[i]}`);
        printUsage();
        process.exit(1);
    }
  }

  return opts;
}

function printUsage() {
  console.log(`
Usage: node contracts/submit-proof.cjs [options]

Submit a Groth16 proof to the SP1Verifier contract on Base Sepolia.

Options:
  --proof <path>        Path to proof.bin (default: proof.bin)
  --rpc-url <url>       Base Sepolia RPC (default: https://sepolia.base.org)
  --contract <address>  SP1Verifier contract address (reads from deployed-address.txt if omitted)
  --vkey <hex>          Program verification key (bytes32). Overrides SP1_VKEY env.
  --public-inputs <hex> Hex-encoded public values (optional)
  --dry-run             Print plan without sending transaction
  --help                Show this usage message

Environment:
  SP1_VKEY              Program verification key hex (bytes32)
  PRIVATE_KEY           Required: deployer wallet private key

Examples:
  node contracts/submit-proof.cjs --proof proof.bin
  node contracts/submit-proof.cjs --dry-run --proof /tmp/proof.bin
  SP1_VKEY=0x... node contracts/submit-proof.cjs
`);
}

// ── Proof File Parsing ────────────────────────────────────────────────

/**
 * Parse a bincode-serialized SP1ProofWithVKey and extract:
 *   - programVKey (bytes32): from the last 32 bytes of the file (SP1VerificationKey.hash)
 *   - proofBytes: the Groth16 proof points + public inputs for on-chain verification
 *   - publicValues: from the public inputs if not provided explicitly
 *
 * Bincode layout (SP1 v3.x Groth16):
 *   [0..4)    enum discriminant (LE u32, Groth16 = 1)
 *   [4..68)   a point (G1, 64 bytes)
 *   [68..196) b point (G2, 128 bytes)
 *   [196..260) c point (G1, 64 bytes)
 *   [260..268) public_inputs length (LE u64)
 *   [268..)   public_inputs data (length × 32 bytes)
 *   ...       Groth16VerificationKey fields (alpha_g1, beta_g2, gamma_g2, delta_g2, ic)
 *   [-32..)    hash (programVKey bytes32)
 */
function parseProofFile(filePath) {
  const data = fs.readFileSync(filePath);
  const len = data.length;

  if (len < 260 + 8 + 32) {
    throw new Error(
      `Proof file too small (${len} bytes). Expected at least 300 bytes for a valid SP1ProofWithVKey.`
    );
  }

  // ── Extract programVKey from last 32 bytes ──
  const programVKey = '0x' + Buffer.from(data.subarray(len - 32)).toString('hex');

  // ── Parse the Groth16 proof portion ──
  // Skip the 4-byte enum discriminant
  const GROTH16_DISCRIMINANT_SIZE = 4;

  // Read the 256 bytes of curve points (a: 64, b: 128, c: 64)
  const curvePoints = data.subarray(GROTH16_DISCRIMINANT_SIZE, GROTH16_DISCRIMINANT_SIZE + 256);

  // Read public_inputs length (u64 LE)
  const pubInputsLenOffset = GROTH16_DISCRIMINANT_SIZE + 256;
  const pubInputsLen = Number(
    data.readBigUInt64LE(pubInputsLenOffset)
  );

  // Sanity check on public inputs count
  if (pubInputsLen > 100) {
    throw new Error(
      `Unreasonable public input count: ${pubInputsLen}. Expected ≤ 100 for a scoring program.`
    );
  }

  const pubInputsDataOffset = pubInputsLenOffset + 8;
  const pubInputsByteLen = pubInputsLen * 32;

  if (pubInputsDataOffset + pubInputsByteLen > len - 32) {
    throw new Error(
      `Proof file truncated: expected ${pubInputsDataOffset + pubInputsByteLen} bytes for public inputs ` +
      `but file has ${len - 32} bytes before hash. Check proof format.`
    );
  }

  const pubInputsData = data.subarray(pubInputsDataOffset, pubInputsDataOffset + pubInputsByteLen);

  // The proof bytes that verifyProof expects: 256 bytes of curve points + public inputs
  const proofBytes = Buffer.concat([curvePoints, pubInputsData]);

  // Extract the first public input as publicValues (the program's committed output)
  // In SP1, the first public input is typically the hash of the public values
  let publicValues = '';
  if (pubInputsLen > 0) {
    // Use the first public input as an approximation; in practice the host script
    // provides the raw public values separately
    publicValues = '0x' + Buffer.from(pubInputsData.subarray(0, 32)).toString('hex');
  }

  return { programVKey, proofBytes, publicValues };
}

// ── Main ──────────────────────────────────────────────────────────────
async function main() {
  const opts = parseArgs();

  // ── 1. Read proof file ─────────────────────────────────────────────
  // Resolve proof path — handle both /tmp (Unix-style, Git Bash) and absolute/normalized paths
  const proofPathRaw = opts.proof;

  // On Windows, try to normalize Git Bash /tmp to the real Windows temp
  let proofPath = proofPathRaw;
  if (!fs.existsSync(proofPathRaw) && proofPathRaw.startsWith('/tmp/')) {
    const winTemp = process.env.TEMP || process.env.TMP || 'C:\\tmp';
    proofPath = path.join(winTemp, proofPathRaw.slice(5));
  } else if (fs.existsSync(proofPathRaw)) {
    proofPath = proofPathRaw;
  } else {
    proofPath = path.resolve(proofPathRaw);
  }

  if (!fs.existsSync(proofPath)) {
    console.error(`❌ Proof file not found: ${proofPath}`);
    console.error(`   (also tried: ${proofPathRaw})`);
    console.error('   Run the SP1 prover first to generate proof.bin.');
    process.exit(1);
  }

  let programVKey, proofBytes, autoPublicValues;
  try {
    const parsed = parseProofFile(proofPath);
    programVKey = parsed.programVKey;
    proofBytes = parsed.proofBytes;
    autoPublicValues = parsed.publicValues;
  } catch (err) {
    console.error(`❌ Failed to parse proof file: ${err.message}`);
    console.error('   Ensure the file is a valid bincode-serialized SP1ProofWithVKey (Groth16 variant).');
    process.exit(1);
  }

  // ── 2. Resolve programVKey ─────────────────────────────────────────
  // Priority: --vkey > SP1_VKEY env > auto-extracted from proof.bin
  const vkeyHex = opts.vkey || process.env.SP1_VKEY || programVKey;

  // Validate bytes32 format
  const vkeyBytes32 = vkeyHex.startsWith('0x') ? vkeyHex : '0x' + vkeyHex;
  if (!/^0x[0-9a-fA-F]{64}$/.test(vkeyBytes32)) {
    console.error(`❌ Invalid programVKey: ${vkeyHex}`);
    console.error('   Must be a 32-byte hex string (64 hex chars, with or without 0x prefix).');
    console.error('   Provide via --vkey <hex> or SP1_VKEY env var.');
    process.exit(1);
  }

  // ── 3. Resolve contract address ────────────────────────────────────
  let contractAddress = opts.contract;

  if (!contractAddress) {
    const addrPath = path.join(SCRIPT_DIR, 'deployed-address.txt');
    if (fs.existsSync(addrPath)) {
      const addrContent = fs.readFileSync(addrPath, 'utf8').trim();
      // Skip comment lines
      const addrLines = addrContent.split('\n').filter(l => !l.startsWith('#') && l.trim());
      const rawAddr = addrLines.length > 0 ? addrLines[0].trim() : '';

      if (!rawAddr || rawAddr === 'not-yet-deployed' || rawAddr === '0x0' || rawAddr === '0x0000000000000000000000000000000000000000') {
        console.error('❌ Contract not yet deployed.');
        console.error('   The address file (contracts/deployed-address.txt) contains:');
        console.error(`   "${rawAddr || '<empty>'}"`);
        console.error('');
        console.error('   Deploy the SP1Verifier contract first:');
        console.error('   PRIVATE_KEY=0x... node contracts/deploy.cjs');
        console.error('');
        console.error('   Or provide the address via --contract <address>.');
        process.exit(1);
      }

      contractAddress = rawAddr;
    } else {
      console.error('❌ No deployed-address.txt found and no --contract provided.');
      console.error('   Deploy the SP1Verifier contract first or provide an address.');
      process.exit(1);
    }
  }

  // Validate address format
  if (!ethers.isAddress(contractAddress)) {
    console.error(`❌ Invalid contract address: ${contractAddress}`);
    process.exit(1);
  }

  // ── 4. Resolve public inputs ───────────────────────────────────────
  const publicInputsHex = opts.publicInputs || autoPublicValues;

  // ── 5. Connect to RPC ──────────────────────────────────────────────
  if (!process.env.PRIVATE_KEY) {
    console.error('❌ PRIVATE_KEY environment variable required.');
    console.error('   Set it to the deployer wallet private key (with 0x prefix).');
    process.exit(1);
  }

  const provider = new ethers.JsonRpcProvider(opts.rpcUrl, CHAIN_ID);
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  // ── 6. Dry-run output ─────────────────────────────────────────────
  const proofSizeKB = (proofBytes.length / 1024).toFixed(1);

  console.log('═══════════════════════════════════════════════════════════');
  console.log('  SP1 Proof Submission Plan');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`  Proof file:      ${proofPath}`);
  console.log(`  Proof size:      ${proofSizeKB} KB`);
  console.log(`  RPC URL:         ${opts.rpcUrl}`);
  console.log(`  Contract:        ${contractAddress}`);
  console.log(`  Program VKey:    ${vkeyBytes32}`);
  console.log(`  Public Inputs:   ${publicInputsHex ? publicInputsHex.substring(0, 66) + '...' : '<none>'}`);
  console.log(`  Wallet:          ${wallet.address}`);
  console.log(`  Chain ID:        ${CHAIN_ID}`);
  console.log(`  Dry run:         ${opts.dryRun ? 'yes' : 'no'}`);
  console.log('─────────────────────────────────────────────────────────');

  if (opts.dryRun) {
    console.log('  ✅ Dry-run complete. No transaction sent.');
    console.log('═══════════════════════════════════════════════════════════');
    process.exit(0);
  }

  // ── 7. Check network connectivity ──────────────────────────────────
  try {
    const network = await provider.getNetwork();
    if (Number(network.chainId) !== CHAIN_ID) {
      console.error(`❌ Unexpected chain ID: ${network.chainId}. Expected ${CHAIN_ID} (Base Sepolia).`);
      process.exit(1);
    }
    const balance = await provider.getBalance(wallet.address);
    console.log(`  Network:         ${network.name} (chainId: ${network.chainId})`);
    console.log(`  Balance:         ${ethers.formatEther(balance)} ETH`);

    if (balance === 0n) {
      console.error('❌ Wallet has no ETH. Fund the wallet and retry.');
      process.exit(1);
    }
  } catch (err) {
    console.error(`❌ RPC connection failed: ${err.message}`);
    console.error(`   URL: ${opts.rpcUrl}`);
    console.error('   Check network connectivity and RPC URL.');
    process.exit(1);
  }

  // ── 8. Load contract ABI ──────────────────────────────────────────
  const abiPath = path.join(SCRIPT_DIR, 'abi/SP1Verifier.json');
  if (!fs.existsSync(abiPath)) {
    console.error(`❌ ABI file not found: ${abiPath}`);
    process.exit(1);
  }

  const abi = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
  const contract = new ethers.Contract(contractAddress, abi, wallet);

  // ── 9. Call verifyProof as a static call ──────────────────────────
  // verifyProof is a view function (no state change). We use staticCall
  // to verify the proof against the on-chain verifier. If it returns
  // without reverting, the proof is valid.
  const publicValuesBytes = publicInputsHex && publicInputsHex !== '0x'
    ? publicInputsHex
    : '0x';

  console.log('\n  Verifying proof on-chain...');

  try {
    // First estimate gas to get the gas cost
    let gasEstimate;
    try {
      gasEstimate = await contract.verifyProof.estimateGas(
        vkeyBytes32,
        publicValuesBytes,
        '0x' + proofBytes.toString('hex')
      );
    } catch {
      // estimateGas may fail for view functions; fall back to a default
      gasEstimate = 0n;
    }

    // Static call — no state change, returns on success, reverts on failure
    const startTime = Date.now();
    await contract.verifyProof.staticCall(
      vkeyBytes32,
      publicValuesBytes,
      '0x' + proofBytes.toString('hex')
    );
    const durationMs = Date.now() - startTime;

    console.log('');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('  ✅ Proof VERIFIED on-chain');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`  Contract:        ${contractAddress}`);
    console.log(`  Program VKey:    ${vkeyBytes32}`);
    console.log(`  Gas (est.):      ${gasEstimate.toString()}`);
    console.log(`  Duration:        ${durationMs}ms`);
    console.log('═══════════════════════════════════════════════════════════');

  } catch (err) {
    // decode revert reason
    let reason = 'Unknown error';

    if (err.reason) {
      reason = err.reason;
    } else if (err.data) {
      try {
        // Try to decode the revert data from the contract
        reason = contract.interface.parseError(err.data)?.args?.reason || err.data;
      } catch {
        reason = err.data;
      }
    } else if (err.message) {
      // Extract revert reason from error message
      const revertMatch = err.message.match(/reverted with reason string '([^']+)'/);
      if (revertMatch) {
        reason = revertMatch[1];
      } else {
        reason = err.message.split('\n')[0];
      }
    }

    console.error('');
    console.error('═══════════════════════════════════════════════════════════');
    console.error('  ❌ Proof REJECTED by verifier contract');
    console.error('═══════════════════════════════════════════════════════════');
    console.error(`  Contract:        ${contractAddress}`);
    console.error(`  Program VKey:    ${vkeyBytes32}`);
    console.error(`  Revert reason:   ${reason}`);
    console.error('═══════════════════════════════════════════════════════════');
    process.exit(1);
  }
}

main().catch(err => {
  console.error(`\n❌ Unexpected error: ${err.message}`);
  process.exit(1);
});
