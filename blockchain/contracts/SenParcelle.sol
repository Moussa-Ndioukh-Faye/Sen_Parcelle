// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SenParcelle {

    // ═════════════════════════════════════════════
    // ACCESS CONTROL (inline — minimal OpenZeppelin pattern)
    // ═════════════════════════════════════════════

    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;
    bytes32 public constant VALIDATOR_ROLE  = keccak256("VALIDATOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE  = keccak256("EMERGENCY_ROLE");

    mapping(bytes32 => mapping(address => bool)) private _roles;

    event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender);

    modifier onlyRole(bytes32 role) {
        require(_roles[role][msg.sender], "SenParcelle: unauthorized");
        _;
    }

    function _grantRole(bytes32 role, address account) internal {
        if (!_roles[role][account]) {
            _roles[role][account] = true;
            emit RoleGranted(role, account, msg.sender);
        }
    }

    function _revokeRole(bytes32 role, address account) internal {
        if (_roles[role][account]) {
            _roles[role][account] = false;
            emit RoleRevoked(role, account, msg.sender);
        }
    }

    function grantRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(account != address(0), "SenParcelle: invalid account");
        _grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(account != address(0), "SenParcelle: invalid account");
        _revokeRole(role, account);
    }

    function hasRole(bytes32 role, address account) external view returns (bool) {
        return _roles[role][account];
    }

    // ═════════════════════════════════════════════
    // REENTRANCY GUARD (inline)
    // ═════════════════════════════════════════════

    uint256 private _status;
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED     = 2;

    modifier nonReentrant() {
        require(_status != _ENTERED, "SenParcelle: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }

    // ═════════════════════════════════════════════
    // PAUSE
    // ═════════════════════════════════════════════

    bool public paused;

    modifier notPaused() {
        require(!paused, "SenParcelle: contract paused");
        _;
    }

    // ═════════════════════════════════════════════
    // STRUCTURES
    // ═════════════════════════════════════════════

    struct Parcel {
        uint256 parcelId;
        bytes32 documentHash;
        bytes32 ipfsHash;
        address owner;
        string  localisation;
        uint256 superficie;
        uint256 prix;
        uint256 registeredAt;
        bool    active;
    }

    struct OwnershipRecord {
        address from;
        address to;
        uint256 timestamp;
        bytes32 transactionRef;
    }

    // ═════════════════════════════════════════════
    // STORAGE
    // ═════════════════════════════════════════════

    mapping(uint256 => Parcel) public parcels;
    mapping(bytes32 => uint256) public hashToParcelId;
    mapping(uint256 => OwnershipRecord[]) public ownershipHistory;
    mapping(address => uint256[]) public ownerParcels;
    mapping(address => mapping(uint256 => uint256)) public ownerParcelIndex;

    uint256 public totalParcels;
    uint256 public totalTransfers;

    // ═════════════════════════════════════════════
    // EVENTS
    // ═════════════════════════════════════════════

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
    event PaymentReceived(address indexed sender, uint256 amount, uint256 timestamp);

    // ═════════════════════════════════════════════
    // CONSTRUCTOR
    // ═════════════════════════════════════════════

    constructor() {
        _status = _NOT_ENTERED;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VALIDATOR_ROLE,     msg.sender);
        _grantRole(EMERGENCY_ROLE,     msg.sender);
    }

    // ═════════════════════════════════════════════
    // MAIN FUNCTIONS
    // ═════════════════════════════════════════════

    function registerParcel(
        uint256 _parcelId,
        bytes32 _documentHash,
        bytes32 _ipfsHash,
        address _owner,
        string  calldata _localisation,
        uint256 _superficie,
        uint256 _prix
    ) external onlyRole(VALIDATOR_ROLE) notPaused {
        require(_parcelId > 0,                "SenParcelle: invalid parcel id");
        require(_documentHash != bytes32(0),  "SenParcelle: empty document hash");
        require(_owner != address(0),         "SenParcelle: invalid owner");
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
        ownerParcelIndex[_owner][_parcelId] = ownerParcels[_owner].length;
        ownerParcels[_owner].push(_parcelId);
        totalParcels++;

        ownershipHistory[_parcelId].push(OwnershipRecord({
            from:           address(0),
            to:             _owner,
            timestamp:      block.timestamp,
            transactionRef: bytes32(0)
        }));

        emit ParcelRegistered(_parcelId, _documentHash, _owner, _localisation, block.timestamp);
    }

    function transferOwnership(
        uint256 _parcelId,
        address _newOwner,
        bytes32 _txRef
    ) external onlyRole(VALIDATOR_ROLE) notPaused {
        Parcel storage parcel = parcels[_parcelId];

        require(parcel.parcelId != 0,        "SenParcelle: parcel not found");
        require(parcel.active,               "SenParcelle: parcel not active");
        require(_newOwner != address(0),     "SenParcelle: invalid new owner");
        require(_newOwner != parcel.owner,   "SenParcelle: already owner");

        address previousOwner = parcel.owner;

        ownershipHistory[_parcelId].push(OwnershipRecord({
            from:           previousOwner,
            to:             _newOwner,
            timestamp:      block.timestamp,
            transactionRef: _txRef
        }));

        _removeFromOwnerList(_parcelId, previousOwner);

        parcel.owner = _newOwner;
        ownerParcels[_newOwner].push(_parcelId);
        ownerParcelIndex[_newOwner][_parcelId] = ownerParcels[_newOwner].length - 1;
        totalTransfers++;

        emit OwnershipTransferred(_parcelId, previousOwner, _newOwner, _txRef, block.timestamp);
    }

    function updateMetadata(uint256 _parcelId, bytes32 _newIpfsHash)
        external onlyRole(VALIDATOR_ROLE) notPaused
    {
        require(parcels[_parcelId].parcelId != 0, "SenParcelle: not found");
        require(_newIpfsHash != bytes32(0),       "SenParcelle: invalid hash");
        parcels[_parcelId].ipfsHash = _newIpfsHash;
    }

    function revokeParcel(uint256 _parcelId) external onlyRole(EMERGENCY_ROLE) {
        require(parcels[_parcelId].active, "SenParcelle: already revoked");
        Parcel storage p = parcels[_parcelId];
        p.active = false;
        _removeFromOwnerList(_parcelId, p.owner);
        emit ParcelRevoked(_parcelId, msg.sender, block.timestamp);
    }

    function _removeFromOwnerList(uint256 _parcelId, address _owner) internal {
        uint256[] storage list = ownerParcels[_owner];
        uint256 len = list.length;
        uint256 index = ownerParcelIndex[_owner][_parcelId];
        require(index < len && list[index] == _parcelId, "SenParcelle: not in list");

        if (index != len - 1) {
            uint256 lastId = list[len - 1];
            list[index] = lastId;
            ownerParcelIndex[_owner][lastId] = index;
        }

        list.pop();
        delete ownerParcelIndex[_owner][_parcelId];
    }

    // ═════════════════════════════════════════════
    // READ FUNCTIONS (view — free)
    // ═════════════════════════════════════════════

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

    function getParcel(uint256 _parcelId) external view returns (Parcel memory) {
        require(parcels[_parcelId].parcelId != 0, "SenParcelle: not found");
        return parcels[_parcelId];
    }

    function getParcelHistory(uint256 _parcelId)
        external view returns (OwnershipRecord[] memory)
    {
        return ownershipHistory[_parcelId];
    }

    function getOwnerParcels(address _owner)
        external view returns (uint256[] memory)
    {
        return ownerParcels[_owner];
    }

    function isOwner(uint256 _parcelId, address _addr)
        external view returns (bool)
    {
        return parcels[_parcelId].owner == _addr && parcels[_parcelId].active;
    }

    // ═════════════════════════════════════════════
    // EMERGENCY
    // ═════════════════════════════════════════════

    function pause()   external onlyRole(EMERGENCY_ROLE) { paused = true;  emit ContractPaused(true,  block.timestamp); }
    function unpause() external onlyRole(EMERGENCY_ROLE) { paused = false; emit ContractPaused(false, block.timestamp); }

    // ═════════════════════════════════════════════
    // PAYMENTS
    // ═════════════════════════════════════════════

    receive() external payable {
        emit PaymentReceived(msg.sender, msg.value, block.timestamp);
    }

    function withdraw(address payable to) external onlyRole(EMERGENCY_ROLE) nonReentrant {
        uint256 balance = address(this).balance;
        require(balance > 0, "SenParcelle: no balance");
        require(to != address(0), "SenParcelle: invalid address");
        (bool sent, ) = to.call{value: balance}("");
        require(sent, "SenParcelle: transfer failed");
    }
}
