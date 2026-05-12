/**
 * Deploy SP1Verifier contract to Base Sepolia.
 *
 * Idempotent: checks for an existing deployment before attempting.
 *
 * Usage:
 *   PRIVATE_KEY=0x... node contracts/deploy.cjs
 *
 * Required (one of):
 *   PRIVATE_KEY       — deployer private key (with Base Sepolia ETH)
 */
const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

async function main() {
  const RPC_URL = process.env.BASE_SEPOLIA_RPC || 'https://sepolia.base.org';
  const CHAIN_ID = 84532;
  const DEPLOY_ADDR_PATH = path.join(__dirname, 'deployed-address.txt');

  // ── Check if already deployed ───────────────────────────────────────
  if (fs.existsSync(DEPLOY_ADDR_PATH)) {
    const addr = fs.readFileSync(DEPLOY_ADDR_PATH, 'utf8').trim();
    console.log(`⏭  Already deployed at ${addr} (delete contracts/deployed-address.txt to re-deploy)`);
    return;
  }

  // ── Wallet ──────────────────────────────────────────────────────────
  if (!process.env.PRIVATE_KEY) {
    console.error('❌ PRIVATE_KEY environment variable required.');
    console.error('   Generate a wallet, fund it with Base Sepolia ETH, then:');
    console.error('   PRIVATE_KEY=0x... node contracts/deploy.cjs');
    console.error('');
    console.error('   Get test ETH from: https://www.alchemy.com/faucets/base-sepolia');
    process.exit(1);
  }

  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY);

  // ── Provider ────────────────────────────────────────────────────────
  const provider = new ethers.JsonRpcProvider(RPC_URL, CHAIN_ID);
  const network = await provider.getNetwork();
  console.log(`Connected: ${network.name} (chainId: ${network.chainId})`);

  const balance = await provider.getBalance(wallet.address);
  console.log(`Deployer: ${wallet.address} (${ethers.formatEther(balance)} ETH)`);

  if (balance === 0n) {
    console.error('❌ Deployer has no ETH. Fund the wallet and retry.');
    process.exit(1);
  }

  const signer = wallet.connect(provider);

  // ── Load contract ───────────────────────────────────────────────────
  const abi = JSON.parse(fs.readFileSync(path.join(__dirname, 'abi/SP1Verifier.json'), 'utf8'));
  const bytecode = fs.readFileSync(
    path.join(__dirname, 'build/contracts_SP1Verifier_SP1Verifier.bin'), 'utf8'
  ).trim();

  console.log(`Deploying SP1Verifier (${bytecode.length / 2} bytes)...`);

  // ── Deploy ──────────────────────────────────────────────────────────
  const factory = new ethers.ContractFactory(abi, bytecode, signer);
  const contract = await factory.deploy();
  const tx = contract.deploymentTransaction();
  console.log(`  TX: ${tx.hash}`);

  const receipt = await tx.wait();
  const address = await contract.getAddress();

  // ── Save ────────────────────────────────────────────────────────────
  fs.writeFileSync(DEPLOY_ADDR_PATH, `${address}\n`);
  fs.writeFileSync(
    path.join(__dirname, 'deploy-receipt.json'),
    JSON.stringify({
      address,
      txHash: receipt.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString(),
      chainId: CHAIN_ID,
      network: 'base-sepolia',
      deployer: wallet.address,
    }, null, 2)
  );

  console.log(`\n✅ SP1Verifier deployed to Base Sepolia`);
  console.log(`   Address: ${address}`);
  console.log(`   TX: ${receipt.hash}`);
  console.log(`   Block: ${receipt.blockNumber}`);
}

main().catch(err => {
  console.error('Deployment failed:', err.message);
  process.exit(1);
});
