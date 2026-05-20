# ══════════════════════════════════════════════════════════════
# SERVICE AUTH COMPLET
# apps/users/application/services/auth_service.py
# ══════════════════════════════════════════════════════════════

import logging
import re

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service d'authentification centralisé.
    Gère : changement de mot de passe, activation 2FA,
    déconnexion, verrouillage de compte.
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES     = 30

    def __init__(self, user_repo, jwt_service, otp_service, sms_service, audit_service):
        self._users  = user_repo
        self._jwt    = jwt_service
        self._otp    = otp_service
        self._sms    = sms_service
        self._audit  = audit_service

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change le mot de passe.
        Révoque tous les tokens existants après changement.
        """
        from core.exceptions.base import BusinessRuleViolationException, ValidationException

        if not self._users.check_password(user_id, old_password):
            raise BusinessRuleViolationException(
                "Mot de passe actuel incorrect.", "wrong_password"
            )

        if len(new_password) < 12:
            raise ValidationException({"new_password": "Minimum 12 caractères."})
        if not re.search(r"[A-Z]", new_password):
            raise ValidationException({"new_password": "Doit contenir une majuscule."})
        if not re.search(r"[a-z]", new_password):
            raise ValidationException({"new_password": "Doit contenir une minuscule."})
        if not re.search(r"\d", new_password):
            raise ValidationException({"new_password": "Doit contenir un chiffre."})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
            raise ValidationException({"new_password": "Doit contenir un caractère spécial."})

        if old_password == new_password:
            raise ValidationException({"new_password": "Le nouveau mot de passe doit être différent."})

        self._users.set_password(user_id, new_password)

        # ─── Révoquer tous les tokens → forcer reconnexion ───
        self._jwt.revoke_all_for_user(user_id)
        self._audit.log(user_id, "password_changed", {})
        logger.info(f"Mot de passe changé : user={user_id}")
        return True

    def enable_2fa(self, user_id: str, phone: str) -> dict:
        """
        Active le 2FA par SMS.
        Envoie un code de confirmation pour valider le téléphone.
        """
        otp_code = self._otp.generate(user_id, purpose="enable_2fa")

        user_entity = self._users.get_by_id(user_id)
        self._sms.send(
            to=str(user_entity.telephone),
            message=f"Sen_parcelle : code d'activation 2FA : {otp_code}. Valable 5 minutes."
        )
        return {"message": "Code de confirmation envoyé par SMS."}

    def confirm_2fa(self, user_id: str, otp_code: str) -> bool:
        """Confirme le 2FA après vérification OTP."""
        if self._otp.verify(user_id, otp_code, purpose="enable_2fa"):
            from apps.users.infrastructure.models import User as UserORM
            UserORM.objects.filter(id=user_id).update(is_2fa_enabled=True)
            self._audit.log(user_id, "2fa_enabled", {})
            return True
        return False

    def disable_2fa(self, user_id: str, password: str) -> bool:
        """Désactive le 2FA (requiert mot de passe actuel)."""
        if not self._users.check_password(user_id, password):
            from core.exceptions.base import BusinessRuleViolationException
            raise BusinessRuleViolationException("Mot de passe incorrect.", "wrong_password")

        from apps.users.infrastructure.models import User as UserORM
        UserORM.objects.filter(id=user_id).update(is_2fa_enabled=False)
        self._audit.log(user_id, "2fa_disabled", {})
        return True

    def logout(self, user_id: str, access_token_jti: str, refresh_token: str | None = None):
        """
        Déconnexion : révoque les tokens.
        """
        self._jwt.revoke(access_token_jti)
        if refresh_token:
            from apps.users.application.services.jwt_service import JWTService
            jwt_svc = JWTService()
            payload = jwt_svc.validate_refresh(refresh_token)
            if payload:
                self._jwt.revoke(payload["jti"], ttl=7 * 24 * 3600)
        self._audit.log(user_id, "logout", {})

    def handle_failed_login(self, user_id: str):
        """
        Incrémente les tentatives échouées.
        Verrouille le compte après MAX_FAILED_ATTEMPTS.
        """
        from datetime import timedelta

        from django.db.models import F
        from django.utils import timezone

        from apps.users.infrastructure.models import User as UserORM

        # Incrément atomique via F() — pas de race condition
        updated = UserORM.objects.filter(id=user_id).update(
            failed_attempts=F("failed_attempts") + 1
        )
        if not updated:
            return

        # Recharger pour vérifier le seuil
        user_orm = UserORM.objects.get(id=user_id)
        if user_orm.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            # Verrouiller (update atomique pour éviter double-lock)
            UserORM.objects.filter(
                id=user_id,
                locked_until__isnull=True
            ).update(
                locked_until=timezone.now() + timedelta(minutes=self.LOCKOUT_MINUTES)
            )
            logger.warning(f"Compte verrouillé : user={user_id}")
            self._audit.log(user_id, "account_locked", {
                "attempts": user_orm.failed_attempts
            })
            # SMS d'alerte
            try:
                self._sms.send(
                    to=str(user_orm.telephone),
                    message=(
                        "⚠️ Sen_parcelle : Votre compte a été temporairement verrouillé "
                        f"suite à {self.MAX_FAILED_ATTEMPTS} tentatives échouées. "
                        f"Réessayez dans {self.LOCKOUT_MINUTES} minutes."
                    )
                )
            except Exception:
                logger.warning(f"Échec d'envoi SMS d'alerte verrouillage user={user_id}")

    def is_account_locked(self, user_id: str) -> bool:
        """Vérifie si un compte est verrouillé."""
        from django.utils import timezone

        from apps.users.infrastructure.models import User as UserORM
        try:
            user_orm = UserORM.objects.get(id=user_id)
            if user_orm.locked_until and user_orm.locked_until > timezone.now():
                return True
            # Déverrouiller automatiquement si le délai est passé
            if user_orm.locked_until and user_orm.locked_until <= timezone.now():
                UserORM.objects.filter(id=user_id).update(
                    locked_until=None, failed_attempts=0
                )
        except UserORM.DoesNotExist:
            pass
        return False

    def reset_failed_attempts(self, user_id: str):
        """Réinitialise les tentatives après une connexion réussie."""
        from apps.users.infrastructure.models import User as UserORM
        UserORM.objects.filter(id=user_id).update(failed_attempts=0, locked_until=None)
