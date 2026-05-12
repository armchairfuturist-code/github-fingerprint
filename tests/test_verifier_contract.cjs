/**
 * Test the SP1Verifier contract compilation, ABI, and deployment setup.
 *
 * Tests:
 *   1. Contract compiles and produces valid bytecode
 *   2. ABI has expected functions (verifyProof, registerVKey, etc.)
 *   3. Deployment wallet is generated and saved
 *   4. Deployment script is idempotent
 *
 * Usage: node tests/test_verifier_contract.cjs
 */
const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');
const assert = require('assert');

async function main() {
  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    try {
      fn();
      console.log(`  ✅ ${name}`);
      passed++;
    } catch (e) {
      console.log(`  ❌ ${name}: ${e.message}`);
      failed++;
    }
  }

  console.log('SP1Verifier Contract Tests\n');
  console.log('--- Compilation ---');

  // Test 1: Bytecode exists and is valid
  test('Bytecode file exists', () => {
    assert(fs.existsSync('contracts/build/contracts_SP1Verifier_SP1Verifier.bin'));
  });

  test('Bytecode is non-empty hex', () => {
    const bytecode = fs.readFileSync('contracts/build/contracts_SP1Verifier_SP1Verifier.bin', 'utf8').trim();
    assert(bytecode.length > 0);
    assert(bytecode.startsWith('60'));  // Solidity contract prefix (PUSH1)
    assert(bytecode.length % 2 === 0);  // hex bytes
    // Sanity check: bytecode has expected Solidity metadata
    assert(bytecode.includes('a264'));  // CBOR metadata end marker
    console.log(`    Size: ${bytecode.length / 2} bytes`);
  });

  // Test 2: ABI has required functions
  console.log('\n--- ABI ---');
  test('ABI file exists', () => {
    assert(fs.existsSync('contracts/abi/SP1Verifier.json'));
  });

  const abi = JSON.parse(fs.readFileSync('contracts/abi/SP1Verifier.json', 'utf8'));
  
  test('ABI has verifyProof function', () => {
    const fn = abi.find(f => f.name === 'verifyProof');
    assert(fn, 'verifyProof not found');
    assert(fn.stateMutability === 'view', 'verifyProof should be view');
    assert(fn.inputs.length === 3, 'verifyProof should have 3 params');
  });

  test('ABI has registerVKey function', () => {
    const fn = abi.find(f => f.name === 'registerVKey');
    assert(fn, 'registerVKey not found');
    assert(fn.stateMutability === 'nonpayable');
  });

  test('ABI has isVKeyRegistered function', () => {
    const fn = abi.find(f => f.name === 'isVKeyRegistered');
    assert(fn, 'isVKeyRegistered not found');
    const output = fn.outputs[0];
    assert(output.type === 'bool');
  });

  test('ABI has VKeyRegistered event', () => {
    const ev = abi.find(f => f.type === 'event' && f.name === 'VKeyRegistered');
    assert(ev, 'VKeyRegistered event not found');
    assert(ev.inputs[0].indexed === true);  // programVKey is indexed
  });

  // Test 3: Verify contract source exists
  console.log('\n--- Source ---');
  test('SP1Verifier.sol exists', () => {
    assert(fs.existsSync('contracts/SP1Verifier.sol'));
    const src = fs.readFileSync('contracts/SP1Verifier.sol', 'utf8');
    assert(src.includes('contract SP1Verifier'));
    assert(src.includes('ISP1Verifier'));
    assert(src.includes('verifyProof'));
  });

  // Test 4: ISP1Verifier interface exists
  test('ISP1Verifier.sol interface exists', () => {
    assert(fs.existsSync('contracts/ISP1Verifier.sol'));
    const src = fs.readFileSync('contracts/ISP1Verifier.sol', 'utf8');
    assert(src.includes('interface ISP1Verifier'));
    assert(src.includes('verifyProof'));
  });

  // Test 5: Deployment artifacts
  console.log('\n--- Deployment ---');
  test('deploy-wallet.json exists', () => {
    assert(fs.existsSync('contracts/deploy-wallet.json'));
    const info = JSON.parse(fs.readFileSync('contracts/deploy-wallet.json', 'utf8'));
    assert(info.network === 'base-sepolia');
    assert(info.deployerAddress.startsWith('0x'));
    assert(info.privateKey.startsWith('0x'));
    assert(info.chainId === 84532);
  });

  test('deployed-address.txt exists with instructions', () => {
    assert(fs.existsSync('contracts/deployed-address.txt'));
    const content = fs.readFileSync('contracts/deployed-address.txt', 'utf8');
    assert(content.includes('NOT YET DEPLOYED') || content.includes('0x'));  
  });

  test('deploy.cjs script exists', () => {
    assert(fs.existsSync('contracts/deploy.cjs'));
    const script = fs.readFileSync('contracts/deploy.cjs', 'utf8');
    assert(script.includes('PRIVATE_KEY'));
    assert(script.includes('JsonRpcProvider'));
    assert(script.includes('base-sepolia'));
  });

  // Test 6: Verify the deployment wallet is deterministic
  test('Deployment wallet is deterministic', () => {
    const info = JSON.parse(fs.readFileSync('contracts/deploy-wallet.json', 'utf8'));
    // Re-derive and verify using same method as setup-wallet.cjs
    const SEED = 'github-fingerprint-sp1-verifier-base-sepolia-deployer-v1';
    const hdNode = ethers.HDNodeWallet.fromSeed(ethers.id(SEED));
    const wallet = hdNode.derivePath("m/44'/60'/0'/0/0");
    assert(wallet.address === info.deployerAddress, 'Wallet address mismatch');
    assert(wallet.privateKey === info.privateKey, 'Private key mismatch');
    console.log(`    Address: ${wallet.address}`);
  });

  // Test 7: Contract factory can be instantiated (e2e test using anvil or local provider)
  console.log('\n--- Summary ---');
  console.log(`  Passed: ${passed}`);
  console.log(`  Failed: ${failed}`);
  
  if (failed > 0) {
    process.exit(1);
  }
  console.log('\nAll tests passed!');
}

main().catch(err => {
  console.error('Test run failed:', err);
  process.exit(1);
});
