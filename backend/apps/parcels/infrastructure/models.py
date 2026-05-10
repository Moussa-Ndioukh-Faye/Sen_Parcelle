# ══════════════════════════════════════════════════════════════
# INFRASTRUCTURE : models.py (PostGIS)
# ══════════════════════════════════════════════════════════════

import uuid as uuid_lib
from typing import List, Optional
from django.db import models

try:
    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point
    HAS_GIS = True
except Exception:
    HAS_GIS = False
    gis_models = None
    Point = None

from core.models.base import BaseModel, TimeStampedModel
from apps.parcels.domain.entities import ParcelEntity, GeoPoint, ParcelStatus, IParcelRepository


class Parcel(BaseModel):
    """
    Modèle ORM Parcelle avec PostGIS pour les coordonnées GPS.
    PostGIS permet : recherche géographique, calcul de distance,
    détection de doublons par proximité.
    """

    STATUS_CHOICES = [
        ("pending",   "En attente"),
        ("validated", "Validée"),
        ("certified", "Certifiée"),
        ("rejected",  "Rejetée"),
        ("sold",      "Vendue"),
    ]

    REGION_CHOICES = [
        ("Dakar",        "Dakar"),
        ("Thiès",        "Thiès"),
        ("Saint-Louis",  "Saint-Louis"),
        ("Ziguinchor",   "Ziguinchor"),
        ("Kaolack",      "Kaolack"),
        ("Diourbel",     "Diourbel"),
        ("Louga",        "Louga"),
        ("Fatick",       "Fatick"),
        ("Kolda",        "Kolda"),
        ("Tambacounda",  "Tambacounda"),
        ("Kaffrine",     "Kaffrine"),
        ("Matam",        "Matam"),
        ("Kédougou",     "Kédougou"),
        ("Sédhiou",      "Sédhiou"),
    ]

    # ─── Propriétaire ───
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,        # Ne jamais supprimer une parcelle si user supprimé
        related_name="parcels",
        db_index=True,
    )

    # ─── Infos de base ───
    titre       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    region      = models.CharField(max_length=50, choices=REGION_CHOICES, db_index=True)
    surface     = models.FloatField(help_text="Superficie en m²")
    price       = models.DecimalField(max_digits=14, decimal_places=2, help_text="Prix en FCFA")
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)

    # ─── PostGIS : coordonnées géographiques ───
    if HAS_GIS:
        location = gis_models.PointField(
            geography=True,        # Calculs en mètres (pas degrés)
            srid=4326,             # WGS84 (GPS standard)
            null=True, blank=True,
            help_text="Point GPS (longitude, latitude)"
        )
    else:
        location = models.JSONField(
            null=True, blank=True,
            help_text="Point GPS (longitude, latitude) - FALLBACK (GDAL missing)"
        )

    # ─── Blockchain & Documents ───
    document_hash      = models.CharField(max_length=64,  blank=True, db_index=True)   # SHA-256
    ipfs_hash          = models.CharField(max_length=100, blank=True)                   # CID IPFS
    blockchain_tx_hash = models.CharField(max_length=100, blank=True, db_index=True)   # TX Polygon
    certified_at       = models.DateTimeField(null=True, blank=True)

    # ─── Validation admin ───
    validated_by  = models.ForeignKey(
        "users.User", null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="validated_parcels"
    )
    validated_at  = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "parcels"
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["status", "region"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["document_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.titre} [{self.status}] — {self.region}"

    # ─── Mapping domaine ↔ ORM ───

    def to_domain(self) -> ParcelEntity:
        loc = None
        if self.location:
            if HAS_GIS:
                # Point PostGIS : (longitude, latitude)
                loc = GeoPoint(latitude=self.location.y, longitude=self.location.x)
            else:
                # Fallback JSON : {"latitude": 1.23, "longitude": 4.56}
                if isinstance(self.location, dict):
                    loc = GeoPoint(latitude=self.location.get("latitude"), longitude=self.location.get("longitude"))

        return ParcelEntity(
            id=str(self.id),
            owner_id=str(self.owner_id),
            titre=self.titre,
            description=self.description,
            location=loc,
            region=self.region,
            surface=self.surface,
            price=float(self.price),
            status=ParcelStatus(self.status),
            document_hash=self.document_hash or None,
            ipfs_hash=self.ipfs_hash or None,
            blockchain_tx_hash=self.blockchain_tx_hash or None,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: ParcelEntity) -> "Parcel":
        point = None
        if entity.location:
            if HAS_GIS:
                # PostGIS Point : Point(longitude, latitude)
                point = Point(entity.location.longitude, entity.location.latitude, srid=4326)
            else:
                # Fallback JSON
                point = {"latitude": entity.location.latitude, "longitude": entity.location.longitude}

        return cls(
            id=entity.id,
            titre=entity.titre,
            description=entity.description,
            region=entity.region,
            surface=entity.surface,
            price=entity.price,
            status=entity.status.value,
            location=point,
            document_hash=entity.document_hash or "",
            ipfs_hash=entity.ipfs_hash or "",
            blockchain_tx_hash=entity.blockchain_tx_hash or "",
        )


# ──────────────────────────────────────────────────────────────
# MODÈLE : Photos de parcelles
# ──────────────────────────────────────────────────────────────

class ParcelPhoto(TimeStampedModel):
    parcel      = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="photos")
    file_key    = models.CharField(max_length=255)   # Clé S3
    url         = models.URLField()
    is_primary  = models.BooleanField(default=False)
    file_hash   = models.CharField(max_length=64)    # SHA-256 avant upload

    class Meta:
        db_table = "parcel_photos"


# ──────────────────────────────────────────────────────────────
# REPOSITORY DJANGO avec PostGIS
# ──────────────────────────────────────────────────────────────

try:
    from django.contrib.gis.measure import Distance
    from django.contrib.gis.geos import Point as GeoPoint_ORM
except Exception:
    Distance = None
    GeoPoint_ORM = None


class DjangoParcelRepository(IParcelRepository):
    """Implémentation PostGIS du repository Parcel."""

    def get_by_id(self, parcel_id: str) -> Optional[ParcelEntity]:
        try:
            return Parcel.objects.get(id=parcel_id).to_domain()
        except Parcel.DoesNotExist:
            return None

    def save(self, entity: ParcelEntity) -> ParcelEntity:
        parcel_orm = Parcel.from_domain(entity)
        # owner_id est un FK, à assigner séparément
        parcel_orm.owner_id = entity.owner_id
        parcel_orm.save()
        return parcel_orm.to_domain()

    def find_nearby(self, location: GeoPoint, radius_m: float) -> List[ParcelEntity]:
        """Utilise PostGIS pour trouver les parcelles dans un rayon."""
        if not HAS_GIS:
            return []
            
        point = GeoPoint_ORM(location.longitude, location.latitude, srid=4326)
        qs = Parcel.objects.filter(
            location__distance_lte=(point, Distance(m=radius_m))
        ).exclude(status="rejected")
        return [p.to_domain() for p in qs]

    def find_nearby_active(self, location: GeoPoint, radius_m: float) -> List[ParcelEntity]:
        """Parcelles actives (pending, validated, certified, sold) dans un rayon."""
        if not HAS_GIS:
            return []
            
        point = GeoPoint_ORM(location.longitude, location.latitude, srid=4326)
        qs = Parcel.objects.filter(
            location__distance_lte=(point, Distance(m=radius_m)),
            status__in=["pending", "validated", "certified", "sold"],
        )
        return [p.to_domain() for p in qs]

    def find_by_region(self, region: Optional[str], status: Optional[str] = None) -> List[ParcelEntity]:
        qs = Parcel.objects.all()
        if region:
            qs = qs.filter(region=region)
        if status:
            qs = qs.filter(status=status)
        return [p.to_domain() for p in qs]

    def find_by_owner(self, owner_id: str) -> List[ParcelEntity]:
        return [p.to_domain() for p in Parcel.objects.filter(owner_id=owner_id)]

    def exists_near(self, location: GeoPoint, radius_m: float = 50.0) -> bool:
        if not HAS_GIS:
            return False
            
        point = GeoPoint_ORM(location.longitude, location.latitude, srid=4326)
        return Parcel.objects.filter(
            location__distance_lte=(point, Distance(m=radius_m)),
            status__in=["pending", "validated", "certified"],
        ).exists()