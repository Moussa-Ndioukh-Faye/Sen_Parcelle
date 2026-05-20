from dataclasses import dataclass

from apps.users.domain.repositories import IUserRepository

# ══════════════════════════════════════════════════════════════
# apps/users/application/use_cases/login.py
# UC : Connexion avec 2FA OTP
# ══════════════════════════════════════════════════════════════

@dataclass
class LoginInput:
    email:    str
    password: str
    otp_code: str | None = None    # Requis si is_2fa_enabled


@dataclass
class LoginOutput:
    access_token:  str
    refresh_token: str
    user_id:       str
    role:          str
    requires_otp:  bool = False       # True → renvoyer avec le code OTP


class LoginUseCase:
    """
    UC: Connexion.

    Flux :
    1. Vérifier email + password
    2. Si 2FA activé → exiger OTP
    3. Vérifier OTP si fourni
    4. Générer tokens JWT
    5. Logger l'événement d'audit
    """

    def __init__(self, user_repository: IUserRepository,
                 otp_service, jwt_service, audit_service, sms_service,
                 auth_service=None):
        self._users  = user_repository
        self._otp    = otp_service
        self._jwt    = jwt_service
        self._audit  = audit_service
        self._sms    = sms_service
        self._auth   = auth_service

    def execute(self, data: LoginInput) -> LoginOutput:
        from core.exceptions.base import BusinessRuleViolationException, InvalidOTPException

        # ─── 1. Récupérer l'utilisateur (message générique anti-énumération) ───
        user_entity = self._users.get_by_email(data.email)
        if user_entity is None:
            await_sleep = __import__("time").sleep
            await_sleep(0.5)
            raise BusinessRuleViolationException(
                "Email ou mot de passe incorrect.", "invalid_credentials"
            )

        # ─── 2. Vérifier verrouillage compte ───
        if self._auth and self._auth.is_account_locked(user_entity.id):
            raise BusinessRuleViolationException(
                "Compte temporairement verrouillé. Réessayez dans 30 minutes.",
                "account_locked"
            )

        # ─── 3. Vérifier compte actif ───
        if not user_entity.is_active:
            raise BusinessRuleViolationException(
                "Compte désactivé. Contactez le support.", "account_disabled"
            )

        # ─── 4. Vérifier le mot de passe (via infrastructure) ───
        if not self._users.check_password(user_entity.id, data.password):
            self._audit.log(user_entity.id, "login_failed", {"reason": "bad_password"})
            if self._auth:
                self._auth.handle_failed_login(user_entity.id)
            raise BusinessRuleViolationException(
                "Email ou mot de passe incorrect.", "invalid_credentials"
            )

        # ─── 5. Reset failed attempts après succès ───
        if self._auth:
            self._auth.reset_failed_attempts(user_entity.id)

        # ─── 6. 2FA : OTP requis ───
        if user_entity.is_2fa_enabled:
            if not data.otp_code:
                # Envoyer OTP + demander code
                otp = self._otp.generate(user_entity.id, purpose="login")
                self._sms.send(
                    to=str(user_entity.telephone),
                    message=f"Sen_parcelle : code de connexion {otp}. Valable 5 minutes."
                )
                return LoginOutput(
                    access_token="",
                    refresh_token="",
                    user_id=user_entity.id,
                    role=user_entity.role.value,
                    requires_otp=True,
                )

            # Valider l'OTP fourni
            if not self._otp.verify(user_entity.id, data.otp_code, purpose="login"):
                self._audit.log(user_entity.id, "login_failed", {"reason": "bad_otp"})
                raise InvalidOTPException()

        # ─── 7. Générer tokens JWT ───
        tokens = self._jwt.generate(user_id=user_entity.id, role=user_entity.role.value)

        # ─── 8. Audit ───
        self._audit.log(user_entity.id, "login_success", {})

        return LoginOutput(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
            user_id=user_entity.id,
            role=user_entity.role.value,
        )
