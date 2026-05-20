import logging
from dataclasses import dataclass

from apps.users.domain.repositories import IUserRepository

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# apps/users/application/use_cases/verify_kyc.py
# UC : Vérification KYC par admin
# ══════════════════════════════════════════════════════════════

@dataclass
class VerifyKYCInput:
    user_id:    str
    admin_id:   str
    decision:   str       # "approve" | "reject"
    reason:     str = ""  # Raison du rejet


@dataclass
class VerifyKYCOutput:
    user_id:    str
    kyc_status: str
    message:    str


class VerifyKYCUseCase:
    """
    UC: L'admin valide ou rejette le KYC d'un utilisateur.
    Envoie une notification SMS au résultat.
    """

    def __init__(self, user_repository: IUserRepository,
                 sms_service, audit_service):
        self._users  = user_repository
        self._sms    = sms_service
        self._audit  = audit_service

    def execute(self, data: VerifyKYCInput) -> VerifyKYCOutput:
        from core.exceptions.base import BusinessRuleViolationException, EntityNotFoundException

        user = self._users.get_by_id(data.user_id)
        if user is None:
            raise EntityNotFoundException("Utilisateur", data.user_id)

        if user.kyc_status.value == "verified":
            raise BusinessRuleViolationException(
                "Cet utilisateur est déjà vérifié.", "already_verified"
            )

        # Appliquer la décision
        if data.decision == "approve":
            updated_user = user.verify_kyc()
            sms_msg = (
                "✅ Votre identité a été vérifiée sur Sen_parcelle."
                " Vous pouvez maintenant publier des parcelles."
            )
            # Marquer kyc_verified_at
            from django.utils import timezone

            from apps.users.infrastructure.models import User as UserORM
            UserORM.objects.filter(id=data.user_id).update(kyc_verified_at=timezone.now())
        elif data.decision == "reject":
            updated_user = user.reject_kyc()
            reason_msg   = f" Raison : {data.reason}" if data.reason else ""
            sms_msg      = f"❌ Votre vérification d'identité a été refusée.{reason_msg} Contactez le support."
        else:
            raise BusinessRuleViolationException("Décision invalide : approve ou reject.", "invalid_decision")

        self._users.save(updated_user)

        # Notification SMS
        try:
            self._sms.send(to=str(user.telephone), message=sms_msg)
        except Exception as e:
            logger.warning(f"Échec envoi SMS KYC user={user.id}: {e}")

        # Audit
        self._audit.log(data.admin_id, "kyc_decision", {
            "target_user": data.user_id,
            "decision": data.decision,
            "reason": data.reason,
        })

        return VerifyKYCOutput(
            user_id=user.id,
            kyc_status=updated_user.kyc_status.value,
            message=f"KYC {'approuvé' if data.decision == 'approve' else 'rejeté'} avec succès.",
        )
