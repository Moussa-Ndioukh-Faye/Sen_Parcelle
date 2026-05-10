"""
apps/parcels/domain/entities.py + infrastructure/models.py
-----------------------------------------------------------
Domaine Parcelles : entité pure + modèle PostGIS + repository.
"""

# ══════════════════════════════════════════════════════════════
# DOMAIN : entities.py
# ══════════════════════════════════════════════════════════════

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class ParcelStatus(str, Enum):
    PENDING   = "pending"     # Soumise, en attente admin
    VALIDATED = "validated"   # Validée, pas encore blockchain
    CERTIFIED = "certified"   # Enregistrée sur blockchain
    REJECTED  = "rejected"    # Rejetée par admin
    SOLD      = "sold"        # Vendue


@dataclass(frozen=True)
class GeoPoint:
    """Coordonnées GPS validées."""
    latitude:  float
    longitude: float

    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude invalide : {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude invalide : {self.longitude}")

    def distance_to_meters(self, other: "GeoPoint") -> float:
        """
        Distance approx. en mètres (formule Haversine).
        Utilisé pour la détection de doublons (fraude).
        """
        import math
        R = 6371000  # Rayon Terre en mètres
        phi1 = math.radians(self.latitude)
        phi2 = math.radians(other.latitude)
        dphi = math.radians(other.latitude - self.latitude)
        dlam = math.radians(other.longitude - self.longitude)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return R * 2 * math.asin(math.sqrt(a))


@dataclass
class ParcelEntity:
    """Entité Parcelle — règles métier pures."""
    id:                  str
    owner_id:            str
    titre:               str
    description:         str
    location:            GeoPoint
    region:              str
    surface:             float        # m²
    price:               float        # FCFA
    status:              ParcelStatus = ParcelStatus.PENDING
    document_hash:       Optional[str] = None   # SHA-256 du titre foncier
    ipfs_hash:           Optional[str] = None   # Hash IPFS
    blockchain_tx_hash:  Optional[str] = None   # TX Polygon
    created_at:          Optional[datetime] = None

    # ─── Règles métier ───

    def can_be_validated(self) -> bool:
        """Une parcelle peut être validée seulement si elle est en attente."""
        return self.status == ParcelStatus.PENDING

    def can_be_purchased(self) -> bool:
        """Une parcelle est achetable seulement si elle est certifiée."""
        return self.status == ParcelStatus.CERTIFIED

    def is_near(self, other_location: GeoPoint, threshold_m: float = 50.0) -> bool:
        """
        Détecte si deux parcelles sont à moins de `threshold_m` mètres.
        Utilisé par le FraudService pour détecter les doublons.
        Seuil par défaut : 50 mètres.
        """
        return self.location.distance_to_meters(other_location) < threshold_m

    def validate(self) -> "ParcelEntity":
        """L'admin valide la parcelle."""
        from dataclasses import replace
        if not self.can_be_validated():
            raise ValueError(f"Impossible de valider : statut actuel = {self.status}")
        return replace(self, status=ParcelStatus.VALIDATED)

    def certify(self, tx_hash: str, ipfs_hash: str) -> "ParcelEntity":
        """Certification blockchain après validation."""
        from dataclasses import replace
        return replace(
            self,
            status=ParcelStatus.CERTIFIED,
            blockchain_tx_hash=tx_hash,
            ipfs_hash=ipfs_hash,
        )

    def reject(self) -> "ParcelEntity":
        from dataclasses import replace
        return replace(self, status=ParcelStatus.REJECTED)

    def mark_sold(self) -> "ParcelEntity":
        from dataclasses import replace
        return replace(self, status=ParcelStatus.SOLD)


# ──────────────────────────────────────────────────────────────
# REPOSITORY INTERFACE
# ──────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import List


class IParcelRepository(ABC):

    @abstractmethod
    def get_by_id(self, parcel_id: str) -> Optional[ParcelEntity]: ...

    @abstractmethod
    def save(self, parcel: ParcelEntity) -> ParcelEntity: ...

    @abstractmethod
    def find_nearby(self, location: GeoPoint, radius_m: float) -> List[ParcelEntity]:
        """Parcelles dans un rayon donné (PostGIS)."""
        ...

    @abstractmethod
    def find_nearby_active(self, location: GeoPoint, radius_m: float) -> List[ParcelEntity]:
        """Parcelles actives (non-rejetées) dans un rayon donné."""
        ...

    @abstractmethod
    def find_by_region(self, region: str, status: Optional[str] = None) -> List[ParcelEntity]: ...

    @abstractmethod
    def find_by_owner(self, owner_id: str) -> List[ParcelEntity]: ...

    @abstractmethod
    def exists_near(self, location: GeoPoint, radius_m: float = 50.0) -> bool:
        """Vérifie si une parcelle existe déjà à proximité (anti-fraude)."""
        ...