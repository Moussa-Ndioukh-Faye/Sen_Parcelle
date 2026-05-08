# ════════════════════════════════════════════════════════════════
# SERVICE BLOCKCHAIN DJANGO
# apps/blockchain/application/services/blockchain_service.py
# ════════════════════════════════════════════════════════════════

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CertificationResult:
    """Résultat d'une certification blockchain."""
    tx_hash:       str
    ipfs_hash:     str
    block_number:  int
    gas_used:      int
    contract_address: str


@dataclass
class VerificationResult:
    """Résultat d'une vérification de certificat."""
    is_valid:       bool
    parcel_id:      Optional[int]
    owner_address:  Optional[str]
    registered_at:  Optional[int]   # timestamp
    message:        str


class BlockchainService:
    """
    Service central blockchain pour Sen_parcelle.
    Orchestre : IPFS upload → Polygon enregistrement.
    """

    def __init__(self, polygon_adapter, ipfs_adapter):
        self._polygon = polygon_adapter
        self._ipfs    = ipfs_adapter

    def certify_parcel(self, parcel, admin_wallet: str) -> CertificationResult:
        """
        Certifie une parcelle sur Polygon.

        Flux :
        1. Générer hash SHA-256 du document
        2. Uploader métadonnées sur IPFS
        3. Enregistrer sur Polygon
        4. Retourner résultat

        Args:
            parcel: ParcelEntity
            admin_wallet: Adresse wallet admin (propriétaire contrat)
        """
        from django.utils import timezone

        # ─── 1. Hash du document ───
        document_hash_hex = parcel.document_hash or self._compute_parcel_hash(parcel)

        # Convertir en bytes32 pour Solidity
        doc_hash_bytes32 = bytes.fromhex(document_hash_hex.replace("0x", ""))
        if len(doc_hash_bytes32) < 32:
            doc_hash_bytes32 = doc_hash_bytes32.ljust(32, b'\x00')

        # ─── 2. Upload IPFS ───
        metadata = {
            "parcel_id":     parcel.id,
            "document_hash": document_hash_hex,
            "titre":         parcel.titre,
            "region":        parcel.region,
            "surface":       parcel.surface,
            "owner_id":      parcel.owner_id,
            "certified_at":  timezone.now().isoformat(),
            "platform":      "Sen_parcelle · Sénégal",
        }
        ipfs_cid = self._ipfs.pin_metadata(metadata)
        ipfs_hash_bytes32 = self._str_to_bytes32(ipfs_cid)

        # ─── 3. Adresse wallet du propriétaire ───
        owner_address = self._get_or_create_wallet(parcel.owner_id)

        # ─── 4. Enregistrer sur Polygon ───
        result = self._polygon.register_parcel(
            parcel_id=self._parcel_id_to_uint(parcel.id),
            document_hash=doc_hash_bytes32,
            ipfs_hash=ipfs_hash_bytes32,
            owner_address=owner_address,
            localisation=f"{parcel.region}, Sénégal",
            superficie=int(parcel.surface),
            prix=int(parcel.price) if parcel.price else 0,
        )

        logger.info(
            f"Parcelle certifiée : id={parcel.id} "
            f"tx={result['tx_hash']} ipfs={ipfs_cid}"
        )

        return CertificationResult(
            tx_hash=result["tx_hash"],
            ipfs_hash=ipfs_cid,
            block_number=result["block_number"],
            gas_used=result.get("gas_used", 0),
            contract_address=result.get("contract_address", ""),
        )

    def verify_certificate(self, document_hash_hex: str) -> VerificationResult:
        """
        Vérifie un certificat sur la blockchain (lecture gratuite).
        """
        try:
            doc_hash_bytes32 = bytes.fromhex(document_hash_hex.replace("0x", ""))
            if len(doc_hash_bytes32) < 32:
                doc_hash_bytes32 = doc_hash_bytes32.ljust(32, b'\x00')

            result = self._polygon.verify_document(doc_hash_bytes32)

            if not result["valid"]:
                return VerificationResult(
                    is_valid=False,
                    parcel_id=None,
                    owner_address=None,
                    registered_at=None,
                    message="Certificat introuvable ou révoqué.",
                )

            return VerificationResult(
                is_valid=True,
                parcel_id=result["parcel_id"],
                owner_address=result["owner"],
                registered_at=result["registered_at"],
                message="Certificat valide — enregistré sur Polygon.",
            )
        except Exception as e:
            logger.error(f"Erreur vérification certificat : {e}")
            return VerificationResult(
                is_valid=False,
                parcel_id=None,
                owner_address=None,
                registered_at=None,
                message=f"Erreur de vérification : {str(e)}",
            )

    def transfer_ownership(
        self,
        parcel_id_str:   str,
        new_owner_id:    str,
        transaction_ref: str,
    ) -> dict:
        """
        Transfère la propriété d'une parcelle sur Polygon.
        Appelé après confirmation du paiement.
        """
        parcel_id_uint = self._parcel_id_to_uint(parcel_id_str)
        new_owner_addr = self._get_or_create_wallet(new_owner_id)
        tx_ref_bytes32 = self._str_to_bytes32(transaction_ref)

        result = self._polygon.transfer_ownership(
            parcel_id=parcel_id_uint,
            new_owner=new_owner_addr,
            tx_ref=tx_ref_bytes32,
        )
        logger.info(
            f"Propriété transférée blockchain : parcel={parcel_id_str} "
            f"new_owner={new_owner_id} tx={result['tx_hash']}"
        )
        return result

    # ─── Helpers ───

    def _compute_parcel_hash(self, parcel) -> str:
        """Génère un hash SHA-256 à partir des données de la parcelle."""
        data = f"{parcel.id}-{parcel.titre}-{parcel.owner_id}-{parcel.surface}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _parcel_id_to_uint(self, parcel_id_str: str) -> int:
        """
        Convertit un UUID Django en uint256 pour Solidity.
        Les UUID sont sur 128 bits, ils tiennent parfaitement dans uint256.
        """
        import uuid
        try:
            uid = uuid.UUID(parcel_id_str)
            return uid.int
        except ValueError:
            return abs(hash(parcel_id_str))

    def _str_to_bytes32(self, s: str) -> bytes:
        """Convertit une chaîne en bytes32 pour Solidity."""
        encoded = s.encode("utf-8")[:32]
        return encoded.ljust(32, b'\x00')

    def _get_or_create_wallet(self, user_id: str) -> str:
        """
        Retourne l'adresse wallet d'un utilisateur.
        Si l'utilisateur n'a pas de wallet, utilise l'adresse admin du contrat.
        En V2 : générer un wallet déterministe par user_id.
        """
        from apps.users.infrastructure.models import User as UserORM
        try:
            user = UserORM.objects.get(id=user_id)
            wallet = getattr(user, "wallet_address", None)
            if wallet:
                return wallet
        except UserORM.DoesNotExist:
            pass

        # Fallback : adresse admin (propriétaire du contrat)
        from django.conf import settings
        from web3 import Web3
        w3      = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        account = w3.eth.account.from_key(settings.POLYGON_PRIVATE_KEY)
        return account.address