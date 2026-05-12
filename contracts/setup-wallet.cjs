/**
 * Generate a deterministic deployment wallet for Base Sepolia.
 * Saves the address and instructions for funding.
 *
 * The wallet is derived from a fixed seed so it can be regenerated.
 */
const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

function main() {
  const SEED = 'github-fingerprint-sp1-verifier-base-sepolia-deployer-v1';
  const hdNode = ethers.HDNodeWallet.fromSeed(ethers.id(SEED));
  const wallet = hdNode.derivePath("m/44'/60'/0'/0/0");

  const info = {
    network: 'base-sepolia',
    chainId: 84532,
    deployerAddress: wallet.address,
    privateKey: wallet.privateKey,
    requiredETH: '~0.01',
    faucets: [
      'https://www.alchemy.com/faucets/base-sepolia',
      'https://base-sepolia-faucet.vercel.app/',
      'https://www.coinbase.com/faucets/base-sepolia-faucet',
    ],
    deployCommand: 'PRIVATE_KEY=' + wallet.privateKey + ' node contracts/deploy.cjs',
    notes: 'Fund deployerAddress with ~0.01 Base Sepolia ETH, then run the deploy command.',
  };

  console.log(JSON.stringify(info, null, 2));

  // Save wallet info
  fs.writeFileSync(
    path.join(__dirname, 'deploy-wallet.json'),
    JSON.stringify(info, null, 2)
  );

  // Save the wallet address as a placeholder (will be replaced after actual deployment)
  fs.writeFileSync(
    path.join(__dirname, 'deployed-address.txt'),
    `# SP1Verifier deployment address for Base Sepolia
# Status: NOT YET DEPLOYED
# 
# To deploy:
#   1. Fund ${wallet.address} with ~0.01 Base Sepolia ETH
#   2. Run: PRIVATE_KEY=${wallet.privateKey} node contracts/deploy.cjs
#   3. This file will be updated with the contract address.
#
# Base Sepolia ETH faucets:
#   - https://www.alchemy.com/faucets/base-sepolia
#   - https://base-sepolia-faucet.vercel.app/
#   - https://www.coinbase.com/faucets/base-sepolia-faucet
#
not-yet-deployed
`
  );

  console.log('\nDeployment wallet info saved to contracts/deploy-wallet.json');
  console.log(`Deployer address: ${wallet.address}`);
}

main();
