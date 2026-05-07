"""
apps/users/application/services/kyc_service.py
-----------------------------------------------
Service KYC (Know Your Customer) pour Sen_parcelle.
Processus :
1. Utilisateur uploade CNI/Passeport
2. Hash SHA-256 du document calculé + stocké
3. Admin reçoit notification
4. Admin approuve ou rejette
5. SMS de confirmation envoyé
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class KYCSubmissionInput:
    user_id:        str
    document_type:  str          # "cni" | "passeport" | "permis"
    document_bytes: bytes        # Contenu binaire du document
    document_name:  str
    selfie_bytes:   Optional[bytes] = None   # Photo selfie (optionnel V1)


@dataclass
class KYCSubmissionOutput:
    submission_id:  str
    document_hash:  str
    message:        str


class KYCService:
    """
    Service de gestion du processus KYC.

    Flux complet :
    Utilisateur → upload doc → hash → S3 → notif admin
    Admin → approve/reject → SMS user → mise à jour statut
    """

    ALLOWED_TYPES    = {"cni", "passeport", "permis"}
    MAX_FILE_SIZE_MB = 10

    def __init__(self, user_repo, storage_service, sms_service,
                 notification_service, audit_service):
        self._users         = user_repo
        self._storage       = storage_service
        self._sms           = sms_service
        self._notifications = notification_service
        self._audit         = audit_service

    def submit_kyc(self, data: KYCSubmissionInput) -> KYCSubmissionOutput:
        """
        L'utilisateur soumet ses documents KYC.
        """
        from core.exceptions.base import (
            EntityNotFoundException, BusinessRuleViolationException, ValidationException
        )

        # ─── Validation ───
        if data.document_type not in self.ALLOWED_TYPES:
            raise ValidationException({
                "document_type": f"Type invalide. Acceptés : {self.ALLOWED_TYPES}"
            })

        size_mb = len(data.document_bytes) / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise ValidationException({
                "document": f"Fichier trop volumineux ({size_mb:.1f}MB). Maximum : {self.MAX_FILE_SIZE_MB}MB"
            })

        # ─── Vérifier utilisateur ───
        user = self._users.get_by_id(data.user_id)
        if user is None:
            raise EntityNotFoundException("Utilisateur", data.user_id)

        if user.kyc_status.value == "verified":
            raise BusinessRuleViolationException(
                "Votre identité est déjà vérifiée.", "already_verified"
            )

        # ─── Hash SHA-256 du document ───
        document_hash = hashlib.sha256(data.document_bytes).hexdigest()

        # ─── Upload S3 (chemin sécurisé, non public) ───
        s3_key = (
            f"kyc/{data.user_id}/"
            f"{data.document_type}/"
            f"{document_hash[:16]}_{data.document_name}"
        )
        self._storage.upload_private(
            content=data.document_bytes,
            key=s3_key,
            content_type="application/pdf" if data.document_name.endswith(".pdf") else "image/jpeg",
        )

        # ─── Mettre à jour le hash en base ───
        from apps.users.infrastructure.models import User as UserORM
        UserORM.objects.filter(id=data.user_id).update(
            kyc_document_hash=document_hash,
            kyc_status="pending",
        )

        # ─── Notifier les admins ───
        self._notifications.notify_admins(
            event="kyc_pending",
            data={
                "user_id":       data.user_id,
                "user_nom":      user.nom,
                "document_type": data.document_type,
                "document_hash": document_hash,
            }
        )

        # ─── Audit ───
        self._audit.log(data.user_id, "kyc_submitted", {
            "document_type": data.document_type,
            "document_hash": document_hash,
        })

        submission_id = str(uuid.uuid4())
        logger.info(f"KYC soumis : user={data.user_id} hash={document_hash[:16]}...")

        return KYCSubmissionOutput(
            submission_id=submission_id,
            document_hash=document_hash,
            message="Documents KYC soumis avec succès. Vous serez notifié par SMS sous 24h.",
        )

    def get_kyc_status(self, user_id: str) -> dict:
        """Retourne le statut KYC détaillé d'un utilisateur."""
        from core.exceptions.base import EntityNotFoundException
        from apps.users.infrastructure.models import User as UserORM

        try:
            user_orm = UserORM.objects.get(id=user_id)
        except UserORM.DoesNotExist:
            raise EntityNotFoundException("Utilisateur", user_id)

        return {
            "kyc_status":       user_orm.kyc_status,
            "has_document":     bool(user_orm.kyc_document_hash),
            "verified_at":      user_orm.kyc_verified_at,
            "message":          self._get_status_message(user_orm.kyc_status),
        }

    @staticmethod
    def _get_status_message(status: str) -> str:
        messages = {
            "pending":  "Vos documents sont en cours de vérification (sous 24h).",
            "verified": "✅ Identité vérifiée. Vous pouvez publier des parcelles.",
            "rejected": "❌ Documents refusés. Veuillez soumettre des documents valides.",
        }
        return messages.get(status, "Statut inconnu.")