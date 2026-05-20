# ══════════════════════════════════════════════════════════════
# ADAPTER POLYGON
# apps/blockchain/infrastructure/adapters/polygon_adapter.py
# ══════════════════════════════════════════════════════════════

class PolygonAdapter:
    """
    Adapter Web3.py pour interagir avec le smart contract Polygon.
    """

    def __init__(self):
        from django.conf import settings
        from web3 import Web3

        self._w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        self._account = self._w3.eth.account.from_key(settings.POLYGON_PRIVATE_KEY)

        # ABI du contrat SenParcelle.sol
        self._contract = self._w3.eth.contract(
            address=settings.POLYGON_CONTRACT_ADDRESS,
            abi=self._load_abi(),
        )

    def register_parcel(self, parcel_id: str, document_hash: str,
                        ipfs_hash: str, owner_address: str,
                        localisation: str, superficie: int, prix: int) -> dict:
        """Appelle registerParcel() sur le smart contract."""
        try:
            # Conversion UUID -> uint256
            numeric_id = int(parcel_id.replace("-", ""), 16)

            # Conversion hashes -> bytes32
            doc_hash_bytes = self._w3.to_bytes(hexstr=document_hash)
            # CID IPFS est base58, on l'encode en bytes32
            ipfs_hash_bytes = self._str_to_bytes32(ipfs_hash)

            tx = self._contract.functions.registerParcel(
                numeric_id,
                doc_hash_bytes,
                ipfs_hash_bytes,
                owner_address,
                localisation,
                superficie,
                prix,
            ).build_transaction({
                "from":     self._account.address,
                "nonce":    self._w3.eth.get_transaction_count(self._account.address),
                "gas":      400_000,
                "gasPrice": self._w3.eth.gas_price,
            })

            signed  = self._w3.eth.account.sign_transaction(tx, self._account.key)
            tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "tx_hash":      tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used":     receipt.gasUsed,
            }
        except Exception as e:
            from core.exceptions.base import ExternalServiceException
            raise ExternalServiceException("Polygon", str(e))

    def transfer_ownership(self, parcel_id: str, new_owner: str, tx_ref: str = "") -> dict:
        """Appelle transferOwnership() sur le smart contract."""
        try:
            numeric_id = int(parcel_id.replace("-", ""), 16)
            # tx_ref est optionnel, si présent on le convertit en bytes32
            tx_ref_bytes = self._str_to_bytes32(tx_ref) if tx_ref else b'\x00'*32

            tx = self._contract.functions.transferOwnership(
                numeric_id,
                new_owner,
                tx_ref_bytes,
            ).build_transaction({
                "from":     self._account.address,
                "nonce":    self._w3.eth.get_transaction_count(self._account.address),
                "gas":      250_000,
                "gasPrice": self._w3.eth.gas_price,
            })
            signed  = self._w3.eth.account.sign_transaction(tx, self._account.key)
            tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return {"tx_hash": tx_hash.hex(), "block_number": receipt.blockNumber}
        except Exception as e:
            from core.exceptions.base import ExternalServiceException
            raise ExternalServiceException("Polygon", str(e))

    def verify_certificate(self, document_hash: str) -> dict:
        """Vérifie un certificat sur la blockchain (lecture seule — gratuit)."""
        doc_hash_bytes = self._w3.to_bytes(hexstr=document_hash)
        result = self._contract.functions.verifyDocument(doc_hash_bytes).call()
        return {
            "valide":               result[0],
            "parcel_id":            hex(result[1]),
            "owner":                result[2],
            "date_enregistrement":  result[3],
        }

    def _str_to_bytes32(self, s: str) -> bytes:
        encoded = s.encode("utf-8")[:32]
        return encoded.ljust(32, b'\x00')

    def get_owner_address(self, user_id: str) -> str:
        """Retourne l'adresse wallet d'un utilisateur (ou adresse contrat par défaut)."""
        from apps.users.infrastructure.models import User as UserORM
        try:
            user = UserORM.objects.get(id=user_id)
            return getattr(user, "wallet_address", self._account.address)
        except UserORM.DoesNotExist:
            return self._account.address

    @staticmethod
    def _load_abi() -> list:
        """Charge l'ABI depuis le fichier compilé Hardhat."""
        import json
        from pathlib import Path

        from django.conf import settings
        # Chercher dans plusieurs emplacements possibles
        abi_rel = "blockchain/artifacts/contracts/SenParcelle.sol/SenParcelle.json"
        possible_paths = [
            settings.BASE_DIR / abi_rel,
            settings.BASE_DIR.parent / abi_rel,
            Path(settings.BASE_DIR).parent / abi_rel,
        ]
        for abi_path in possible_paths:
            if abi_path.exists():
                with open(abi_path) as f:
                    return json.load(f)["abi"]
        raise FileNotFoundError(
            f"ABI introuvable. Vérifiez que le contrat est compilé. "
            f"Cherché dans: {[str(p) for p in possible_paths]}"
        )
