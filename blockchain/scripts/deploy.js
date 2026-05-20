import { ethers, network } from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  console.log(`\nDeploiement SenParcelle sur ${network.name}\n`);
  const [deployer] = await ethers.getSigners();
  console.log(`Deployer : ${deployer.address}`);

  const SenParcelle = await ethers.getContractFactory("SenParcelle");
  const contract    = await SenParcelle.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`Contrat deploye : ${address}`);

  const deployment = { network: network.name, address, deployer: deployer.address, timestamp: new Date().toISOString() };
  fs.writeFileSync(path.join(__dirname, `../artifacts/deployment.${network.name}.json`), JSON.stringify(deployment, null, 2));
  console.log(`Infos sauvegardees`);
}

main().catch(err => { console.error(err); process.exitCode = 1; });
