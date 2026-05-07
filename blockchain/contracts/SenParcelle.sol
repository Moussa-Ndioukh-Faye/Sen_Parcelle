// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// ═══════════════════════════════════════════════════════════════
// SenParcelle.sol
// Registre foncier numérique immuable sur Polygon
// ─────────────────────────────────────────────────────────────
// Fonctions :
//   registerParcel()       → Enregistrer une parcelle certifiée
//   transferOwnership()    → Transférer la propriété
//   revokeParcel()         → Révoquer (fraude détectée)
//   verifyDocument()       → Vérifier un hash document
//   getParcelHistory()     → Historique complet
// ═══════════════════════════════════════════════════════════════

contract SenParcelle {

    // ─── OWNER (admin Polygon) ───
    address public owner;
    bool    public paused;

    modifier onlyOwner() {
        require(msg.sender == owner, "SenParcelle: admin only");
        _;
    }

    modifier notPaused() {
        require(!paused, "SenParcelle: contract paused");
        _;
    }

    // ─────────────────────────────────────────────
    // STRUCTURES
    // ─────────────────────────────────────────────

    struct Parcel {
        uint256 parcelId;          // ID Django
        bytes32 documentHash;      // SHA-256 du titre foncier
        bytes32 ipfsHash;          // CID IPFS (metadata)
        address owner;             // Wallet propriétaire actuel
        string  localisation;      // Région / localisation
        uint256 superficie;        // m²
        uint256 prix;              // FCFA (optionnel)
        uint256 registeredAt;      // Timestamp
        bool    active;            // false = révoqué
    }

    struct OwnershipRecord {
        address from;
        address to;
        uint256 timestamp;
        bytes32 transactionRef;    // Référence tx Django
    }

    // ─────────────────────────────────────────────
    // STORAGE
    // ─────────────────────────────────────────────

    // parcelId → Parcel
    mapping(uint256 => Parcel) public parcels;

    // documentHash → parcelId (vérification rapide)
    mapping(bytes32 => uint256) public hashToParcelId;

    // parcelId → historique des transferts
    mapping(uint256 => OwnershipRecord[]) public ownershipHistory;

    // wallet → liste des parcelIds détenus
    mapping(address => uint256[]) public ownerParcels;

    uint256 public totalParcels;
    uint256 public totalTransfers;

    // ─────────────────────────────────────────────
    // ÉVÉNEMENTS
    // ─────────────────────────────────────────────

    event ParcelRegistered(
        uint256 indexed parcelId,
        bytes32 documentHash,
        address indexed owner,
        string  localisation,
        uint256 timestamp
    );

    event OwnershipTransferred(
        uint256 indexed parcelId,
        address indexed from,
        address indexed to,
        bytes32 transactionRef,
        uint256 timestamp
    );

    event ParcelRevoked(
        uint256 indexed parcelId,
        address revokedBy,
        uint256 timestamp
    );

    event ContractPaused(bool paused, uint256 timestamp);

    // ─────────────────────────────────────────────
    // CONSTRUCTEUR
    // ─────────────────────────────────────────────

    constructor() {
        owner  = msg.sender;
        paused = false;
    }

    // ═════════════════════════════════════════════
    // FONCTIONS PRINCIPALES
    // ═════════════════════════════════════════════

    /**
     * @notice Enregistre une nouvelle parcelle certifiée
     * @param _parcelId      ID unique Django
     * @param _documentHash  SHA-256 du titre foncier (bytes32)
     * @param _ipfsHash      CID IPFS des métadonnées
     * @param _owner         Adresse wallet du propriétaire
     * @param _localisation  Localisation textuelle
     * @param _superficie    Surface en m²
     * @param _prix          Prix en FCFA
     */
    function registerParcel(
        uint256 _parcelId,
        bytes32 _documentHash,
        bytes32 _ipfsHash,
        address _owner,
        string  calldata _localisation,
        uint256 _superficie,
        uint256 _prix
    ) external onlyOwner notPaused {
        require(_parcelId > 0,           "SenParcelle: invalid parcel id");
        require(_documentHash != bytes32(0), "SenParcelle: empty document hash");
        require(_owner != address(0),    "SenParcelle: invalid owner");
        require(parcels[_parcelId].parcelId == 0, "SenParcelle: already registered");
        require(hashToParcelId[_documentHash] == 0, "SenParcelle: hash already exists");

        parcels[_parcelId] = Parcel({
            parcelId:     _parcelId,
            documentHash: _documentHash,
            ipfsHash:     _ipfsHash,
            owner:        _owner,
            localisation: _localisation,
            superficie:   _superficie,
            prix:         _prix,
            registeredAt: block.timestamp,
            active:       true
        });

        hashToParcelId[_documentHash] = _parcelId;
        ownerParcels[_owner].push(_parcelId);
        totalParcels++;

        // Premier enregistrement dans l'historique
        ownershipHistory[_parcelId].push(OwnershipRecord({
            from:           address(0),
            to:             _owner,
            timestamp:      block.timestamp,
            transactionRef: bytes32(0)
        }));

        emit ParcelRegistered(
            _parcelId, _documentHash, _owner, _localisation, block.timestamp
        );
    }

    /**
     * @notice Transfère la propriété d'une parcelle après paiement confirmé
     * @param _parcelId      ID de la parcelle
     * @param _newOwner      Nouveau propriétaire
     * @param _txRef         Référence transaction Django/paiement
     */
    function transferOwnership(
        uint256 _parcelId,
        address _newOwner,
        bytes32 _txRef
    ) external onlyOwner notPaused {
        Parcel storage parcel = parcels[_parcelId];

        require(parcel.active,               "SenParcelle: parcel not active");
        require(parcel.parcelId != 0,        "SenParcelle: parcel not found");
        require(_newOwner != address(0),     "SenParcelle: invalid new owner");
        require(_newOwner != parcel.owner,   "SenParcelle: already owner");

        address previousOwner = parcel.owner;

        // Enregistrer dans l'historique
        ownershipHistory[_parcelId].push(OwnershipRecord({
            from:           previousOwner,
            to:             _newOwner,
            timestamp:      block.timestamp,
            transactionRef: _txRef
        }));

        // Mise à jour propriétaire
        parcel.owner = _newOwner;
        ownerParcels[_newOwner].push(_parcelId);
        totalTransfers++;

        emit OwnershipTransferred(
            _parcelId, previousOwner, _newOwner, _txRef, block.timestamp
        );
    }

    /**
     * @notice Met à jour le CID IPFS des métadonnées d'une parcelle
     */
    function updateMetadata(uint256 _parcelId, bytes32 _newIpfsHash) 
        external onlyOwner notPaused 
    {
        require(parcels[_parcelId].parcelId != 0, "SenParcelle: not found");
        require(_newIpfsHash != bytes32(0),       "SenParcelle: invalid hash");
        
        parcels[_parcelId].ipfsHash = _newIpfsHash;
    }

    /**
     * @notice Révoque une parcelle (fraude détectée)
     */
    function revokeParcel(uint256 _parcelId) external onlyOwner {
        require(parcels[_parcelId].active, "SenParcelle: already revoked");
        parcels[_parcelId].active = false;
        emit ParcelRevoked(_parcelId, msg.sender, block.timestamp);
    }

    // ═════════════════════════════════════════════
    // FONCTIONS DE LECTURE (view — gratuites)
    // ═════════════════════════════════════════════

    /**
     * @notice Vérifie un hash de document
     * @return valid       true si le hash est enregistré et actif
     * @return parcelId    ID de la parcelle
     * @return ownerAddr   Adresse du propriétaire actuel
     * @return registeredAt Timestamp d'enregistrement
     */
    function verifyDocument(bytes32 _documentHash) external view returns (
        bool    valid,
        uint256 parcelId,
        address ownerAddr,
        uint256 registeredAt
    ) {
        uint256 pid = hashToParcelId[_documentHash];
        if (pid == 0) return (false, 0, address(0), 0);

        Parcel storage p = parcels[pid];
        return (p.active, p.parcelId, p.owner, p.registeredAt);
    }

    /**
     * @notice Retourne les infos complètes d'une parcelle
     */
    function getParcel(uint256 _parcelId) external view returns (Parcel memory) {
        require(parcels[_parcelId].parcelId != 0, "SenParcelle: not found");
        return parcels[_parcelId];
    }

    /**
     * @notice Retourne l'historique complet des propriétaires
     */
    function getParcelHistory(uint256 _parcelId)
        external view
        returns (OwnershipRecord[] memory)
    {
        return ownershipHistory[_parcelId];
    }

    /**
     * @notice Retourne les parcelles d'un propriétaire
     */
    function getOwnerParcels(address _owner)
        external view
        returns (uint256[] memory)
    {
        return ownerParcels[_owner];
    }

    /**
     * @notice Vérifie si une adresse est propriétaire d'une parcelle
     */
    function isOwner(uint256 _parcelId, address _addr)
        external view
        returns (bool)
    {
        return parcels[_parcelId].owner == _addr && parcels[_parcelId].active;
    }

    // ═════════════════════════════════════════════
    // ADMIN
    // ═════════════════════════════════════════════

    function pause()   external onlyOwner { paused = true;  emit ContractPaused(true,  block.timestamp); }
    function unpause() external onlyOwner { paused = false; emit ContractPaused(false, block.timestamp); }

    function transferContractOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "SenParcelle: invalid address");
        owner = _newOwner;
    }

    // ─── Recevoir MATIC (si nécessaire pour gas) ───
    receive() external payable {}
    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}
