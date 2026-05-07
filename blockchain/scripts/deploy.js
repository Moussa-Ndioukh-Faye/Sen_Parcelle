const { ethers, network } = require("hardhat");
const fs   = require("fs");
const path = require("path");

async function main() {
  console.log(`\n🚀 Déploiement SenParcelle sur ${network.name}\n`);
  const [deployer] = await ethers.getSigners();
  console.log(`📍 Deployer : ${deployer.address}`);

  const SenParcelle = await ethers.getContractFactory("SenParcelle");
  const contract    = await SenParcelle.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`✅ Contrat déployé : ${address}`);

  const deployment = { network: network.name, address, deployer: deployer.address, timestamp: new Date().toISOString() };
  fs.writeFileSync(path.join(__dirname, `../artifacts/deployment.${network.name}.json`), JSON.stringify(deployment, null, 2));
  console.log(`💾 Infos sauvegardées`);
}

main().catch(err => { console.error(err); process.exitCode = 1; });
