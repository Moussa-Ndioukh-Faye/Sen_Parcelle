import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config";

const PRIVATE_KEY_MAINNET = process.env.POLYGON_PRIVATE_KEY ?? "0x" + "0".repeat(64);
const PRIVATE_KEY_TESTNET = process.env.MUMBAI_PRIVATE_KEY ?? "0x" + "0".repeat(64);
const POLYGON_RPC = process.env.POLYGON_RPC_URL ?? "";
const MUMBAI_RPC  = process.env.MUMBAI_RPC_URL  ?? "https://rpc-mumbai.maticvigil.com";
const POLYGONSCAN = process.env.POLYGONSCAN_API_KEY ?? "";

export default {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    hardhat: {},
    mumbai: {
      url:      MUMBAI_RPC,
      accounts: [PRIVATE_KEY_TESTNET],
      chainId:  80001,
    },
    polygon: {
      url:      POLYGON_RPC,
      accounts: [PRIVATE_KEY_MAINNET],
      chainId:  137,
    },
  },
  etherscan: {
    apiKey: { polygon: POLYGONSCAN, polygonMumbai: POLYGONSCAN },
  },
};
