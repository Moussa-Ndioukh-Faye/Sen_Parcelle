"""
apps/users/application/services/otp_service.py
-----------------------------------------------
Service OTP (One-Time Password) pour le 2FA Sen_parcelle.
- Codes à 6 chiffres
- Durée de vie : 5 minutes
- Max 3 tentatives (anti-bruteforce)
- Stockage Redis (pas en base → plus rapide, auto-expiration)
"""

import logging
import secrets

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300  # 5 minutes
OTP_MAX_ATTEMPTS = 3  # Tentatives max avant invalidation
OTP_LENGTH = 6  # Chiffres


class OTPService:
    """
    Gestion des codes OTP via Redis.

    Structure Redis :
        otp:{purpose}:{user_id}:code      → "123456"  (TTL 5min)
        otp:{purpose}:{user_id}:attempts  → "2"       (TTL 5min)
    """

    def __init__(self, cache_backend=None):
        self._cache = cache_backend

    def _cache_key(self, user_id: str, purpose: str, field: str) -> str:
        return f"otp:{purpose}:{user_id}:{field}"

    # ──────────────────────────────────────────────
    # GÉNÉRATION
    # ──────────────────────────────────────────────

    def generate(self, user_id: str, purpose: str = "login") -> str:
        """
        Génère un code OTP à 6 chiffres et le stocke dans Redis.

        Args:
            user_id : ID de l'utilisateur
            purpose : "login" | "transaction" | "verification" | "kyc"

        Returns:
            Le code généré (à envoyer par SMS)
        """
        from django.core.cache import cache

        from core.utils.crypto import RateLimitService

        # Rate limit : max 3 générations d'OTP par 10 minutes
        rl = RateLimitService()
        allowed, _ = rl.check_otp(user_id)
        if not allowed:
            from core.exceptions.base import BusinessRuleViolationException

            raise BusinessRuleViolationException(
                "Trop de demandes de code. Réessayez dans 10 minutes.", "otp_rate_limited"
            )

        # Générer code cryptographiquement sûr via secrets
        code = "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])

        # Stocker dans Redis avec TTL
        cache.set(
            self._cache_key(user_id, purpose, "code"),
            code,
            timeout=OTP_TTL_SECONDS,
        )
        # Réinitialiser le compteur de tentatives
        cache.set(
            self._cache_key(user_id, purpose, "attempts"),
            0,
            timeout=OTP_TTL_SECONDS,
        )

        logger.info(f"OTP généré pour user={user_id} purpose={purpose}")
        return code

    # ──────────────────────────────────────────────
    # VALIDATION
    # ──────────────────────────────────────────────

    def verify(self, user_id: str, code: str, purpose: str = "login") -> bool:
        """
        Vérifie un code OTP.

        Règles :
        - Code doit correspondre
        - Max OTP_MAX_ATTEMPTS tentatives
        - Si valide → invalider immédiatement (usage unique)

        Returns:
            True si valide, False sinon
        """
        from django.core.cache import cache

        from core.exceptions.base import BusinessRuleViolationException, InvalidOTPException

        code_key = self._cache_key(user_id, purpose, "code")
        attempts_key = self._cache_key(user_id, purpose, "attempts")

        stored_code = cache.get(code_key)
        if stored_code is None:
            logger.warning(f"OTP expiré ou inexistant : user={user_id}")
            raise InvalidOTPException()

        # Incrément atomique du compteur de tentatives
        try:
            attempts = cache.incr(attempts_key, 1)
        except ValueError:
            # Key expirée entre-temps — invalider OTP
            cache.delete(code_key)
            logger.warning(f"OTP attempts key expiré : user={user_id}")
            raise BusinessRuleViolationException("Code expiré. Demandez un nouveau code.", "otp_expired")
        if attempts > OTP_MAX_ATTEMPTS:
            # Invalider le code
            cache.delete(code_key)
            cache.delete(attempts_key)
            logger.warning(f"OTP bloqué (trop de tentatives) : user={user_id}")
            raise BusinessRuleViolationException(
                "Trop de tentatives incorrectes. Demandez un nouveau code.", "otp_max_attempts"
            )

        # Vérifier le code (comparaison timing-safe)
        import hmac

        if not hmac.compare_digest(str(stored_code), str(code.strip())):
            remaining = OTP_MAX_ATTEMPTS - attempts
            logger.warning(f"OTP incorrect : user={user_id}, tentatives restantes={remaining}")
            raise InvalidOTPException()

        # ✅ Code valide → invalider immédiatement (usage unique)
        cache.delete(code_key)
        cache.delete(attempts_key)
        logger.info(f"OTP validé : user={user_id} purpose={purpose}")
        return True

    def invalidate(self, user_id: str, purpose: str = "login"):
        """Invalide manuellement un OTP (ex: après changement de téléphone)."""
        from django.core.cache import cache

        cache.delete(self._cache_key(user_id, purpose, "code"))
        cache.delete(self._cache_key(user_id, purpose, "attempts"))

    def is_pending(self, user_id: str, purpose: str = "login") -> bool:
        """Vérifie si un OTP est en attente pour cet utilisateur."""
        from django.core.cache import cache

        return cache.get(self._cache_key(user_id, purpose, "code")) is not None
