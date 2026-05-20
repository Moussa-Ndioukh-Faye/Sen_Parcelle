"""
apps/parcels/application/use_cases/
------------------------------------
UC: Soumettre, Valider, Rechercher des parcelles.
Tous les use cases délèguent aux services et repositories.
"""

import hashlib
from dataclasses import dataclass

from apps.parcels.domain.entities import (
    GeoPoint,
    IParcelRepository,
    ParcelEntity,
    ParcelStatus,
    ParcelType,
)
from apps.users.domain.repositories import IUserRepository
from core.exceptions.base import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    InvalidKYCStatusException,
    ParcelFraudSuspectedException,
)

# ══════════════════════════════════════════════════════════════
# UC: Soumettre une parcelle
# ══════════════════════════════════════════════════════════════

@dataclass
class SubmitParcelInput:
    owner_id:       str
    titre:          str
    description:    str
    localisation:   str
    region:         str
    latitude:       float
    longitude:      float
    superficie:     float
    prix:           float
    type_terrain:   str         # Enum value
    document_bytes: bytes       # Contenu du document (PDF/image)
    document_name:  str


@dataclass
class SubmitParcelOutput:
    parcel_id:      str
    status:         str
    document_hash:  str
    message:        str


class SubmitParcelUseCase:
    """
    UC: Un vendeur soumet une nouvelle parcelle.

    Flux :
    1. Vérifier KYC vendeur
    2. Calculer hash SHA-256 du document
    3. Vérifier anti-doublon géographique (50m)
    4. Uploader document sur S3
    5. Créer la parcelle (statut = pending)
    6. Notifier les admins
    """

    FRAUD_RADIUS_METERS = 50.0
    MAX_FILE_SIZE_MB = 20

    def __init__(self, parcel_repo: IParcelRepository, user_repo: IUserRepository,
                 storage_service, notification_service, audit_service):
        self._parcels       = parcel_repo
        self._users         = user_repo
        self._storage       = storage_service
        self._notifications = notification_service
        self._audit         = audit_service

    def execute(self, data: SubmitParcelInput) -> SubmitParcelOutput:
        # ─── 1. Vérifier le vendeur ───
        owner = self._users.get_by_id(data.owner_id)
        if owner is None:
            raise EntityNotFoundException("Utilisateur", data.owner_id)

        if not owner.can_publish_parcel():
            raise InvalidKYCStatusException()

        # ─── 2. Valider coordonnées ───
        try:
            location = GeoPoint(latitude=data.latitude, longitude=data.longitude)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e), "invalid_location")

        # ─── 3. Anti-fraude : doublon géographique ───
        nearby = self._parcels.find_nearby_active(location, self.FRAUD_RADIUS_METERS)
        if nearby:
            dist = location.distance_to_meters(nearby[0].location)
            raise ParcelFraudSuspectedException(dist)

        # ─── 4. Vérifier taille du fichier ───
        if len(data.document_bytes) > self.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise BusinessRuleViolationException(
                f"Le document dépasse la taille maximale de {self.MAX_FILE_SIZE_MB} Mo.",
                "file_too_large"
            )

        # ─── 5. Hash SHA-256 du document ───
        document_hash = hashlib.sha256(data.document_bytes).hexdigest()

        # ─── 6. Upload S3 (async en production → Celery) ───
        import os
        safe_filename = os.path.basename(data.document_name)
        self._storage.upload(
            content=data.document_bytes,
            filename=f"parcels/{data.owner_id}/{document_hash}/{safe_filename}",
            content_type="application/pdf",
        )

        # ─── 7. Créer l'entité ───
        import uuid
        parcel = ParcelEntity(
            id=str(uuid.uuid4()),
            owner_id=data.owner_id,
            titre=data.titre,
            description=data.description,
            localisation=data.localisation,
            location=location,
            region=data.region,
            superficie=data.superficie,
            prix=data.prix,
            type_terrain=ParcelType(data.type_terrain),
            status=ParcelStatus.PENDING,
            document_hash=document_hash,
        )

        saved = self._parcels.save(parcel)

        # ─── 8. Notifier les admins ───
        self._notifications.notify_admins(
            event="new_parcel_pending",
            data={"parcel_id": saved.id, "titre": data.titre, "region": data.region}
        )

        # ─── 9. Audit ───
        self._audit.log(data.owner_id, "parcel_submitted", {"parcel_id": saved.id})

        return SubmitParcelOutput(
            parcel_id=saved.id,
            status=saved.status.value,
            document_hash=document_hash,
            message="Parcelle soumise avec succès. En attente de validation.",
        )


# ══════════════════════════════════════════════════════════════
# UC: Valider + Certifier une parcelle (Admin)
# ══════════════════════════════════════════════════════════════

@dataclass
class ValidateParcelInput:
    parcel_id:  str
    admin_id:   str
    decision:   str     # "approve" | "reject"
    reason:     str = ""


@dataclass
class ValidateParcelOutput:
    parcel_id:       str
    status:          str
    blockchain_hash: str | None
    message:         str


class ValidateParcelUseCase:
    """
    UC: Admin valide ou rejette une parcelle.
    Si approuvée → déclenchement async blockchain (Celery).
    """

    def __init__(self, parcel_repo: IParcelRepository,
                 blockchain_service, notification_service, audit_service, celery_app):
        self._parcels     = parcel_repo
        self._blockchain  = blockchain_service
        self._notify      = notification_service
        self._audit       = audit_service
        self._celery      = celery_app

    def execute(self, data: ValidateParcelInput) -> ValidateParcelOutput:
        parcel = self._parcels.get_by_id(data.parcel_id)
        if parcel is None:
            raise EntityNotFoundException("Parcelle", data.parcel_id)

        if not parcel.can_be_validated():
            raise BusinessRuleViolationException(
                f"Cette parcelle ne peut pas être validée (statut : {parcel.status.value})",
                "invalid_status"
            )

        if data.decision == "approve":
            validated = parcel.validate()
            self._parcels.save(validated)

            # ─── Déléguer la certification blockchain à Celery (async) ───
            self._celery.send_task(
                "blockchain.certify_parcel",
                kwargs={"parcel_id": data.parcel_id, "admin_id": data.admin_id}
            )

            # Notification vendeur
            self._notify.notify_user(
                user_id=parcel.owner_id,
                event="parcel_validated",
                data={"parcel_id": parcel.id, "titre": parcel.titre}
            )

            self._audit.log(data.admin_id, "parcel_approved", {"parcel_id": data.parcel_id})

            return ValidateParcelOutput(
                parcel_id=parcel.id,
                status="validated",
                blockchain_hash=None,  # Sera mis à jour par Celery
                message="Parcelle validée. Certification blockchain en cours...",
            )

        elif data.decision == "reject":
            rejected = parcel.reject()
            self._parcels.save(rejected)

            self._notify.notify_user(
                user_id=parcel.owner_id,
                event="parcel_rejected",
                data={"parcel_id": parcel.id, "reason": data.reason}
            )

            self._audit.log(data.admin_id, "parcel_rejected", {
                "parcel_id": data.parcel_id, "reason": data.reason
            })

            return ValidateParcelOutput(
                parcel_id=parcel.id,
                status="rejected",
                blockchain_hash=None,
                message="Parcelle rejetée.",
            )

        raise BusinessRuleViolationException("Décision invalide.", "invalid_decision")


# ══════════════════════════════════════════════════════════════
# UC: Recherche de parcelles (avec PostGIS)
# ══════════════════════════════════════════════════════════════

@dataclass
class SearchParcelsInput:
    region:         str | None   = None
    min_prix:       float | None = None
    max_prix:       float | None = None
    min_superficie: float | None = None
    type_terrain:   str | None   = None
    latitude:       float | None = None
    longitude:      float | None = None
    radius_km:      float | None = None     # Recherche géographique
    status:         str             = "certified"
    page:           int             = 1
    page_size:      int             = 20


@dataclass
class SearchParcelsOutput:
    parcels:    list[ParcelEntity]
    total:      int
    page:       int
    page_size:  int


class SearchParcelsUseCase:
    """
    UC: Recherche de parcelles avec filtres.
    Supporte la recherche géographique via PostGIS.
    """

    def __init__(self, parcel_repo: IParcelRepository):
        self._parcels = parcel_repo

    def execute(self, data: SearchParcelsInput) -> SearchParcelsOutput:
        # Recherche géographique si coordonnées fournies
        if data.latitude and data.longitude and data.radius_km:
            location = GeoPoint(data.latitude, data.longitude)
            results  = self._parcels.find_nearby(location, data.radius_km * 1000)
        elif data.region:
            results  = self._parcels.find_by_region(data.region, data.status)
        else:
            # Fallback : retourner toutes les parcelles filtrées par statut
            results  = self._parcels.find_by_region(None, data.status)

        # Filtres prix / superficie en mémoire (ou déléguer au repo selon perf)
        if data.min_prix:
            results = [p for p in results if p.prix >= data.min_prix]
        if data.max_prix:
            results = [p for p in results if p.prix <= data.max_prix]
        if data.min_superficie:
            results = [p for p in results if p.superficie >= data.min_superficie]
        if data.type_terrain:
            results = [p for p in results if p.type_terrain == data.type_terrain]

        # Pagination
        total  = len(results)
        start  = (data.page - 1) * data.page_size
        paged  = results[start:start + data.page_size]

        return SearchParcelsOutput(parcels=paged, total=total, page=data.page, page_size=data.page_size)
