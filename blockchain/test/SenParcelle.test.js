import { expect } from "chai";
import { loadFixture } from "@nomicfoundation/hardhat-network-helpers";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { ethers } = require("hardhat");

const VALIDATOR_ROLE = ethers.keccak256(ethers.toUtf8Bytes("VALIDATOR_ROLE"));
const EMERGENCY_ROLE = ethers.keccak256(ethers.toUtf8Bytes("EMERGENCY_ROLE"));

describe("SenParcelle", function () {

  async function deployFixture() {
    const [admin, validator, emergency, vendor, buyer, other] = await ethers.getSigners();
    const SenParcelle = await ethers.getContractFactory("SenParcelle");
    const contract = await SenParcelle.deploy();

    const docHash  = ethers.keccak256(ethers.toUtf8Bytes("titre-foncier-almadies-v1"));
    const ipfsHash = ethers.keccak256(ethers.toUtf8Bytes("QmTestIPFSHash123456789"));

    return { contract, admin, validator, emergency, vendor, buyer, other, docHash, ipfsHash };
  }

  describe("Deployment", function () {
    it("should set deployer as DEFAULT_ADMIN_ROLE", async function () {
      const { contract, admin } = await loadFixture(deployFixture);
      expect(await contract.hasRole(await contract.DEFAULT_ADMIN_ROLE(), admin.address)).to.be.true;
    });

    it("should grant VALIDATOR_ROLE to deployer", async function () {
      const { contract, admin } = await loadFixture(deployFixture);
      expect(await contract.hasRole(VALIDATOR_ROLE, admin.address)).to.be.true;
    });

    it("should grant EMERGENCY_ROLE to deployer", async function () {
      const { contract, admin } = await loadFixture(deployFixture);
      expect(await contract.hasRole(EMERGENCY_ROLE, admin.address)).to.be.true;
    });

    it("should start unpaused", async function () {
      const { contract } = await loadFixture(deployFixture);
      expect(await contract.paused()).to.be.false;
    });
  });

  describe("Role Management", function () {
    it("admin can grant VALIDATOR_ROLE", async function () {
      const { contract, admin, validator } = await loadFixture(deployFixture);
      await contract.grantRole(VALIDATOR_ROLE, validator.address);
      expect(await contract.hasRole(VALIDATOR_ROLE, validator.address)).to.be.true;
    });

    it("admin can revoke VALIDATOR_ROLE", async function () {
      const { contract, admin, validator } = await loadFixture(deployFixture);
      await contract.grantRole(VALIDATOR_ROLE, validator.address);
      await contract.revokeRole(VALIDATOR_ROLE, validator.address);
      expect(await contract.hasRole(VALIDATOR_ROLE, validator.address)).to.be.false;
    });

    it("non-admin cannot grant roles", async function () {
      const { contract, other, validator } = await loadFixture(deployFixture);
      await expect(
        contract.connect(other).grantRole(VALIDATOR_ROLE, validator.address)
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });
  });

  describe("Registration (registerParcel)", function () {
    it("admin (with VALIDATOR_ROLE) can register", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await expect(contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000))
        .to.emit(contract, "ParcelRegistered");
      expect(await contract.totalParcels()).to.equal(1);
    });

    it("validator with granted role can register", async function () {
      const { contract, admin, validator, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.grantRole(VALIDATOR_ROLE, validator.address);
      await expect(
        contract.connect(validator).registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000)
      ).to.emit(contract, "ParcelRegistered");
    });

    it("non-validator cannot register", async function () {
      const { contract, other, docHash, ipfsHash } = await loadFixture(deployFixture);
      await expect(
        contract.connect(other).registerParcel(1, docHash, ipfsHash, other.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });

    it("rejects duplicate parcelId", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await expect(
        contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: already registered");
    });

    it("rejects duplicate document hash", async function () {
      const { contract, vendor, buyer, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      const otherIpfs = ethers.keccak256(ethers.toUtf8Bytes("other-ipfs"));
      await expect(
        contract.registerParcel(2, docHash, otherIpfs, buyer.address, "Thies", 300, 500000)
      ).to.be.revertedWith("SenParcelle: hash already exists");
    });

    it("rejects zero owner address", async function () {
      const { contract, docHash, ipfsHash } = await loadFixture(deployFixture);
      await expect(
        contract.registerParcel(1, docHash, ipfsHash, ethers.ZeroAddress, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: invalid owner");
    });
  });

  describe("Transfer (transferOwnership)", function () {
    async function registerAndGet() {
      const fixture = await loadFixture(deployFixture);
      const { contract, vendor, buyer, docHash, ipfsHash } = fixture;
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      return { ...fixture, parcelId: 1 };
    }

    it("admin can transfer ownership", async function () {
      const { contract, buyer, parcelId } = await registerAndGet();
      const txRef = ethers.keccak256(ethers.toUtf8Bytes("tx-django-001"));
      await expect(contract.transferOwnership(parcelId, buyer.address, txRef))
        .to.emit(contract, "OwnershipTransferred");
      const info = await contract.getParcel(parcelId);
      expect(info.owner).to.equal(buyer.address);
    });

    it("updates history after transfer", async function () {
      const { contract, vendor, buyer, parcelId } = await registerAndGet();
      await contract.transferOwnership(parcelId, buyer.address, ethers.ZeroHash);
      const history = await contract.getParcelHistory(parcelId);
      expect(history.length).to.equal(2);
      expect(history[1].from).to.equal(vendor.address);
      expect(history[1].to).to.equal(buyer.address);
    });

    it("cannot transfer to same owner", async function () {
      const { contract, vendor, parcelId } = await registerAndGet();
      await expect(
        contract.transferOwnership(parcelId, vendor.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: already owner");
    });

    it("cannot transfer revoked parcel", async function () {
      const { contract, vendor, buyer, parcelId } = await registerAndGet();
      await contract.revokeParcel(parcelId);
      await expect(
        contract.transferOwnership(parcelId, buyer.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: parcel not active");
    });

    it("cannot transfer nonexistent parcel", async function () {
      const { contract, buyer } = await loadFixture(deployFixture);
      await expect(
        contract.transferOwnership(999, buyer.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: parcel not found");
    });

    it("non-validator cannot transfer", async function () {
      const { contract, buyer, other, parcelId } = await registerAndGet();
      await expect(
        contract.connect(other).transferOwnership(parcelId, buyer.address, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });
  });

  describe("Revoke", function () {
    async function registerAndGet() {
      const fixture = await loadFixture(deployFixture);
      const { contract, vendor, docHash, ipfsHash } = fixture;
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      return { ...fixture, parcelId: 1 };
    }

    it("admin can revoke parcel", async function () {
      const { contract, parcelId } = await registerAndGet();
      await expect(contract.revokeParcel(parcelId))
        .to.emit(contract, "ParcelRevoked");
      const info = await contract.getParcel(parcelId);
      expect(info.active).to.be.false;
    });

    it("revoked parcel removed from owner list", async function () {
      const { contract, vendor, parcelId } = await registerAndGet();
      await contract.revokeParcel(parcelId);
      const parcels = await contract.getOwnerParcels(vendor.address);
      expect(parcels.length).to.equal(0);
    });

    it("cannot revoke twice", async function () {
      const { contract, parcelId } = await registerAndGet();
      await contract.revokeParcel(parcelId);
      await expect(contract.revokeParcel(parcelId))
        .to.be.revertedWith("SenParcelle: already revoked");
    });

    it("non-emergency cannot revoke", async function () {
      const { contract, other, parcelId } = await registerAndGet();
      await expect(
        contract.connect(other).revokeParcel(parcelId)
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });
  });

  describe("Verification (verifyDocument)", function () {
    it("returns valid for registered document", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      const [valid, pid, ownerAddr] = await contract.verifyDocument(docHash);
      expect(valid).to.be.true;
      expect(pid).to.equal(1);
      expect(ownerAddr).to.equal(vendor.address);
    });

    it("returns invalid for unknown hash", async function () {
      const { contract } = await loadFixture(deployFixture);
      const [valid] = await contract.verifyDocument(ethers.randomBytes(32));
      expect(valid).to.be.false;
    });

    it("returns invalid for revoked document", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await contract.revokeParcel(1);
      const [valid] = await contract.verifyDocument(docHash);
      expect(valid).to.be.false;
    });
  });

  describe("Metadata (updateMetadata)", function () {
    it("validates can update ipfs hash", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      const newIpfs = ethers.keccak256(ethers.toUtf8Bytes("new-ipfs-hash"));
      await contract.updateMetadata(1, newIpfs);
      const info = await contract.getParcel(1);
      expect(info.ipfsHash).to.equal(newIpfs);
    });

    it("rejects update for nonexistent parcel", async function () {
      const { contract } = await loadFixture(deployFixture);
      await expect(
        contract.updateMetadata(999, ethers.randomBytes(32))
      ).to.be.revertedWith("SenParcelle: not found");
    });

    it("rejects empty ipfs hash", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await expect(
        contract.updateMetadata(1, ethers.ZeroHash)
      ).to.be.revertedWith("SenParcelle: invalid hash");
    });

    it("non-validator cannot update metadata", async function () {
      const { contract, vendor, other, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await expect(
        contract.connect(other).updateMetadata(1, ethers.randomBytes(32))
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });
  });

  describe("Read functions", function () {
    it("isOwner returns true for current owner", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      expect(await contract.isOwner(1, vendor.address)).to.be.true;
    });

    it("isOwner returns false for non-owner", async function () {
      const { contract, vendor, buyer, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      expect(await contract.isOwner(1, buyer.address)).to.be.false;
    });

    it("isOwner returns false for revoked parcel", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await contract.revokeParcel(1);
      expect(await contract.isOwner(1, vendor.address)).to.be.false;
    });

    it("getOwnerParcels returns all owned parcels", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      const otherDoc = ethers.keccak256(ethers.toUtf8Bytes("autre-titre"));
      const otherIpfs = ethers.keccak256(ethers.toUtf8Bytes("autre-ipfs"));
      await contract.registerParcel(2, otherDoc, otherIpfs, vendor.address, "Thies", 300, 750000);
      const parcels = await contract.getOwnerParcels(vendor.address);
      expect(parcels.length).to.equal(2);
      expect(parcels[0]).to.equal(1);
      expect(parcels[1]).to.equal(2);
    });

    it("getParcelHistory returns full history", async function () {
      const { contract, vendor, buyer, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000);
      await contract.transferOwnership(1, buyer.address, ethers.ZeroHash);
      const history = await contract.getParcelHistory(1);
      expect(history.length).to.equal(2);
    });
  });

  describe("Pause / Unpause", function () {
    it("admin can pause and unpause", async function () {
      const { contract } = await loadFixture(deployFixture);
      await contract.pause();
      expect(await contract.paused()).to.be.true;
      await contract.unpause();
      expect(await contract.paused()).to.be.false;
    });

    it("blocks register when paused", async function () {
      const { contract, vendor, docHash, ipfsHash } = await loadFixture(deployFixture);
      await contract.pause();
      await expect(
        contract.registerParcel(1, docHash, ipfsHash, vendor.address, "Dakar", 500, 1000000)
      ).to.be.revertedWith("SenParcelle: contract paused");
    });

    it("non-emergency cannot pause", async function () {
      const { contract, other } = await loadFixture(deployFixture);
      await expect(contract.connect(other).pause())
        .to.be.revertedWith("SenParcelle: unauthorized");
    });
  });

  describe("Withdraw", function () {
    it("emergency role can withdraw", async function () {
      const { contract, admin } = await loadFixture(deployFixture);

      await admin.sendTransaction({
        to: await contract.getAddress(),
        value: ethers.parseEther("1.0"),
      });

      expect(await ethers.provider.getBalance(await contract.getAddress())).to.equal(ethers.parseEther("1.0"));

      await contract.withdraw(admin.address);
      expect(await ethers.provider.getBalance(await contract.getAddress())).to.equal(0);
    });

    it("non-emergency cannot withdraw", async function () {
      const { contract, other } = await loadFixture(deployFixture);
      await expect(
        contract.connect(other).withdraw(other.address)
      ).to.be.revertedWith("SenParcelle: unauthorized");
    });
  });
});
