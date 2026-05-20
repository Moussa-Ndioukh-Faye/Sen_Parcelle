# ══════════════════════════════════════════════════════════════
# INFRASTRUCTURE : models.py (PostGIS)
# ══════════════════════════════════════════════════════════════


from django.db import models

from apps.parcels.domain.entities import (
    GeoPoint,
    IParcelRepository,
    ParcelEntity,
    ParcelStatus,
    ParcelType,
)
from core.models.base import BaseModel, TimeStampedModel


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

    TYPE_CHOICES = [
        ("residentiel", "Résidentiel"),
        ("commercial",  "Commercial"),
        ("agricole",    "Agricole"),
        ("industriel",  "Industriel"),
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
    titre        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    localisation = models.CharField(max_length=255, blank=True)
    region       = models.CharField(max_length=50, choices=REGION_CHOICES, db_index=True)
    superficie   = models.FloatField(help_text="Superficie en m²")
    prix         = models.DecimalField(max_digits=14, decimal_places=2, help_text="Prix en FCFA")
    type_terrain = models.CharField(max_length=20, choices=TYPE_CHOICES, default="residentiel", db_index=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)

    # ─── Coordonnées GPS (JSON) ───
    location = models.JSONField(
        null=True, blank=True,
        help_text="Point GPS {latitude, longitude}"
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
        if self.location and isinstance(self.location, dict):
            loc = GeoPoint(latitude=self.location.get("latitude"), longitude=self.location.get("longitude"))

        return ParcelEntity(
            id=str(self.id),
            owner_id=str(self.owner_id),
            titre=self.titre,
            description=self.description,
            location=loc,
            localisation=self.localisation,
            region=self.region,
            superficie=self.superficie,
            prix=float(self.prix),
            type_terrain=ParcelType(self.type_terrain),
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
            point = {"latitude": entity.location.latitude, "longitude": entity.location.longitude}

        return cls(
            id=entity.id,
            titre=entity.titre,
            description=entity.description,
            localisation=entity.localisation,
            region=entity.region,
            superficie=entity.superficie,
            prix=entity.prix,
            type_terrain=entity.type_terrain.value,
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

class DjangoParcelRepository(IParcelRepository):
    """Implémentation repository Parcel (JSON fallback, pas de PostGIS)."""

    def get_by_id(self, parcel_id: str) -> ParcelEntity | None:
        try:
            return Parcel.objects.select_related('owner', 'validated_by').get(id=parcel_id).to_domain()
        except Parcel.DoesNotExist:
            return None

    def save(self, entity: ParcelEntity) -> ParcelEntity:
        parcel_orm = Parcel.from_domain(entity)
        parcel_orm.owner_id = entity.owner_id
        parcel_orm.save()
        return parcel_orm.to_domain()

    def find_nearby(self, location: GeoPoint, radius_m: float) -> list[ParcelEntity]:
        return []

    def find_nearby_active(self, location: GeoPoint, radius_m: float) -> list[ParcelEntity]:
        return []

    def find_by_region(self, region: str | None, status: str | None = None) -> list[ParcelEntity]:
        qs = Parcel.objects.select_related('owner', 'validated_by').all()
        if region:
            qs = qs.filter(region=region)
        if status:
            qs = qs.filter(status=status)
        return [p.to_domain() for p in qs]

    def find_by_owner(self, owner_id: str) -> list[ParcelEntity]:
        return [p.to_domain() for p in Parcel.objects.select_related('owner', 'validated_by').filter(owner_id=owner_id)]

    def exists_near(self, location: GeoPoint, radius_m: float = 50.0) -> bool:
        return False
