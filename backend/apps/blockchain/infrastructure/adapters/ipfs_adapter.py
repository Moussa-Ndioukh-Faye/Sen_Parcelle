"""
apps/blockchain/infrastructure/adapters/ipfs_adapter.py
---------------------------------------------------------
Upload de métadonnées de parcelles sur IPFS via Pinata.
"""

import json
import logging
import requests
from django.conf import settings
from core.exceptions.base import ExternalServiceException

logger = logging.getLogger(__name__)


class IPFSAdapter:
    """
    Adapter IPFS via Pinata (https://pinata.cloud).
    Alternative : nft.storage (gratuit pour les NFT).

    Rôle : stocker les métadonnées de la parcelle
    de façon permanente et décentralisée.
    """

    PINATA_BASE = "https://api.pinata.cloud"
    TIMEOUT     = 30

    def __init__(self):
        self._jwt       = settings.PINATA_JWT
        self._gateway   = getattr(settings, "IPFS_GATEWAY", "https://gateway.pinata.cloud/ipfs")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._jwt}",
            "Content-Type":  "application/json",
        }

    def pin_metadata(self, metadata: dict) -> str:
        """
        Épingle des métadonnées JSON sur IPFS.
        Retourne le CID (Content Identifier).

        metadata exemple :
        {
            "parcel_id":     "abc-123",
            "document_hash": "sha256hex...",
            "titre":         "Terrain Almadies",
            "region":        "Dakar",
            "surface":       500,
            "owner_id":      "user-123",
            "certified_at":  "2024-01-15T10:00:00Z"
        }
        """
        payload = {
            "pinataContent": metadata,
            "pinataMetadata": {
                "name": f"sen-parcelle-{metadata.get('parcel_id', 'unknown')}",
                "keyvalues": {
                    "project":  "sen_parcelle",
                    "type":     "parcel_certificate",
                    "parcelId": str(metadata.get("parcel_id", "")),
                },
            },
        }

        try:
            response = requests.post(
                f"{self.PINATA_BASE}/pinning/pinJSONToIPFS",
                json=payload,
                headers=self._headers(),
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            cid  = data["IpfsHash"]

            logger.info(f"IPFS pinned : cid={cid} parcel={metadata.get('parcel_id')}")
            return cid

        except requests.RequestException as e:
            logger.error(f"Erreur IPFS pin : {e}")
            raise ExternalServiceException("IPFS/Pinata", str(e))

    def get_metadata(self, cid: str) -> dict:
        """Récupère les métadonnées depuis IPFS."""
        try:
            response = requests.get(
                f"{self._gateway}/{cid}",
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ExternalServiceException("IPFS Gateway", str(e))

    def get_gateway_url(self, cid: str) -> str:
        """Retourne l'URL publique d'accès aux métadonnées."""
        base = self._gateway.rstrip("/")
        return f"{base}/{cid}"

    def unpin(self, cid: str) -> bool:
        """Supprime un pin IPFS (en cas de révocation)."""
        try:
            response = requests.delete(
                f"{self.PINATA_BASE}/pinning/unpin/{cid}",
                headers=self._headers(),
                timeout=self.TIMEOUT,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False