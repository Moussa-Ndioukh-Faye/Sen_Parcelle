// ═══════════════════════════════════════════════════════════════
// blockchain/test/SenParcelle.test.js
// Tests complets du smart contract avec Hardhat + ethers.js
// ═══════════════════════════════════════════════════════════════

const { expect }        = require("chai");
const { ethers }        = require("hardhat");
const { loadFixture }   = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("SenParcelle", function () {

  // ─── Fixture : déploiement propre pour chaque test ───
  async function deployFixture() {
    const [admin, vendor, buyer, other] = await ethers.getSigners();
    const SenParcelle = await ethers.getContractFactory("SenParcelle");
    const contract    = await SenParcelle.deploy();

    // Hash de test
    const docHash  = ethers.keccak256(ethers.toUtf8Bytes("titre-foncier-almadies-v1"));
    const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes("QmTestIPFSHash123456789"));

    return { contract, admin, vendor, buyer, other, docHash, ipfsHash };
  }

  describe("Déploiement", function () {
    it("devrait déployer avec le bon owner", async function () {
      const { contract, admin } = await loadFixture(deployFixture);
      expect(await contract.owner()).to.equal(admin.address);
    });

    it("devrait être non-pausé au déploiement", async function () {
      const { contract } = await loadFixture(deployFixture);
      expect(await contract.paused()).to.be.false;
    });

    it("devrait initialiser le compteur à 0", async function () {
      const { contract } = await loadFixture(deployFixture);
      expect(await contract.totalParcels()).to.equal(0);
    });
  });

  describe("Enregistrement (registerParcel)", function () {
    it("admin peut enregistrer une parcelle", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);

      await expect(contract.registerParcel(
        1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000
      )).to.emit(contract, "ParcelRegistered");

      expect(await contract.totalParcels()).to.equal(1);
    });

    it("rejette un doublon (même parcelId)", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);

      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await expect(
        contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: already registered");
    });

    it("rejette si l'adresse est nulle", async function () {
      const { contract, docHash, ipfsHash } = await loadFixture(deployFixture);
      await expect(
        contract.registerParcel(1, docHash, ipfsHash, ethers.ZeroAddress, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: invalid owner");
    });

    it("non-admin ne peut pas enregistrer", async function () {
      const { contract, other, docHash, ipfsHash } = await loadFixture(deployFixture);
      await expect(
        contract.connect(other).registerParcel(1, docHash, ipfsHash, other.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: admin only");
    });
  });

  describe("Transfert (transferOwnership)", function () {
    async function registerAndGet() {
      const fixture = await loadFixture(deployFixture);
      const { contract, vendor, buyer, docHash, ipfsHash } = fixture;

      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      return { ...fixture, parcelId: 1 };
    }

    it("admin peut transférer la propriété", async function () {
      const { contract, buyer, parcelId } = await registerAndGet();
      await expect(contract.transferOwnership(parcelId, buyer.address, ethers.ZeroHash))
        .to.emit(contract, "OwnershipTransferred");

      const info = await contract.getParcel(parcelId);
      expect(info.owner).to.equal(buyer.address);
    });

    it("l'historique est mis à jour", async function () {
      const { contract, vendor, buyer, parcelId } = await registerAndGet();
      await contract.transferOwnership(parcelId, buyer.address, ethers.ZeroHash);

      const history = await contract.getParcelHistory(parcelId);
      expect(history.length).to.equal(2); // vendor + buyer
    });

    it("ne transfère pas si même propriétaire", async function () {
      const { contract, vendor, parcelId } = await registerAndGet();
      await expect(
        contract.transferOwnership(parcelId, vendor.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: already owner");
    });

    it("ne transfère pas si révoqué", async function () {
      const { contract, vendor, buyer, parcelId } = await registerAndGet();
      await contract.revokeParcel(parcelId);
      await expect(
        contract.transferOwnership(parcelId, buyer.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: parcel not active");
    });
  });

  describe("Vérification (verifyDocument)", function () {
    it("retourne les infos pour un document valide", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);

      const [valid, parcelId, ownerAddr, registeredAt] = await contract.verifyDocument(docHash);
      expect(valid).to.be.true;
      expect(ownerAddr).to.equal(vendor.address);
    });

    it("retourne false pour un hash inconnu", async function () {
      const { contract } = await loadFixture(deployFixture);
      const [valid] = await contract.verifyDocument(ethers.randomBytes(32));
      expect(valid).to.be.false;
    });

    it("retourne false pour un hash révoqué", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await contract.revokeParcel(1);

      const [valid] = await contract.verifyDocument(docHash);
      expect(valid).to.be.false;
    });
  });

  describe("Pause", function () {
    it("admin peut pauser", async function () {
      const { contract } = await loadFixture(deployFixture);
      await contract.pause();
      expect(await contract.paused()).to.be.true;
    });

    it("registerParcel bloqué quand pausé", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.pause();

      await expect(
        contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: contract paused");
    });

    it("non-admin ne peut pas pauser", async function () {
      const { contract, other } = await loadFixture(deployFixture);
      await expect(contract.connect(other).pause())
        .to.be.revertedWith("SenParcelle: admin only");
    });
  });
});

// ═══════════════════════════════════════════════════════════════
// Utilitaires
// ═══════════════════════════════════════════════════════════════

async function getTimestamp() {
  const block = await ethers.provider.getBlock("latest");
  return block.timestamp;
}
