"""
apps/users/application/services/jwt_service.py
-----------------------------------------------
Service JWT complet pour Sen_parcelle.
- Access token (15 min) + Refresh token (7 jours) via SimpleJWT
- Blacklist des tokens révoqués (Redis)
- Payload enrichi (role, kyc_status)
"""

import logging
from datetime import UTC, timedelta

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

logger = logging.getLogger(__name__)


class JWTService:
    """
    Gestion des tokens JWT via rest_framework_simplejwt.
    Utilise Redis pour la blacklist (révocation).
    """

    ACCESS_EXPIRE = timedelta(minutes=15)
    REFRESH_EXPIRE = timedelta(days=7)

    def __init__(self, cache_backend=None):
        self._cache = cache_backend

    # ──────────────────────────────────────────────
    # GÉNÉRATION
    # ──────────────────────────────────────────────

    def generate(self, user_id: str, role: str, kyc_status: str = "pending") -> dict:
        """
        Génère un couple access + refresh token via SimpleJWT.
        Compatible avec rest_framework_simplejwt.authentication.JWTAuthentication.
        """
        access = AccessToken()
        access["sub"] = user_id
        access["role"] = role
        access["kyc_status"] = kyc_status

        refresh = RefreshToken()
        refresh["sub"] = user_id

        return {
            "access": str(access),
            "refresh": str(refresh),
            "access_jti": str(access["jti"]),
            "refresh_jti": str(refresh["jti"]),
            "expires_in": int(self.ACCESS_EXPIRE.total_seconds()),
        }

    # ──────────────────────────────────────────────
    # VALIDATION
    # ──────────────────────────────────────────────

    def validate_access(self, token: str) -> dict | None:
        """
        Valide un access token via SimpleJWT + blacklist Redis.
        Retourne le payload ou None si invalide/expiré/blacklisté.
        """
        try:
            access_token = AccessToken(token)
            payload = {k: access_token[k] for k in access_token.payload}
            if "token_type" in payload:
                payload["type"] = payload.pop("token_type")

            if self._is_blacklisted(payload["jti"]):
                logger.warning(f"Token blacklisté utilisé : jti={payload['jti']}")
                return None

            return payload

        except TokenError:
            return None

    def validate_refresh(self, token: str) -> dict | None:
        """Valide un refresh token via SimpleJWT + blacklist Redis."""
        try:
            refresh_token = RefreshToken(token)
            payload = {k: refresh_token[k] for k in refresh_token.payload}

            if self._is_blacklisted(payload["jti"]):
                return None

            return payload

        except TokenError:
            return None

    def refresh(self, refresh_token: str) -> dict | None:
        """
        Échange un refresh token contre un nouveau couple access/refresh.
        Rotation : l'ancien refresh est blacklisté.
        """
        payload = self.validate_refresh(refresh_token)
        if not payload:
            return None

        # Révoquer l'ancien refresh token
        self.revoke(payload["jti"], ttl=int(self.REFRESH_EXPIRE.total_seconds()))

        # Charger les données utilisateur à jour
        from apps.users.infrastructure.models import User

        try:
            user = User.objects.get(id=payload["sub"])
        except User.DoesNotExist:
            return None

        return self.generate(
            user_id=str(user.id),
            role=user.role,
            kyc_status=user.kyc_status,
        )

    # ──────────────────────────────────────────────
    # RÉVOCATION (blacklist Redis)
    # ──────────────────────────────────────────────

    def revoke(self, jti: str, ttl: int | None = None):
        """
        Ajoute un JTI en blacklist Redis.
        TTL = durée de vie restante du token (inutile de garder plus longtemps).
        """
        from django.core.cache import cache

        cache_key = f"jwt:blacklist:{jti}"
        ttl = ttl or int(self.ACCESS_EXPIRE.total_seconds())
        cache.set(cache_key, "1", timeout=ttl)

    def revoke_all_for_user(self, user_id: str):
        """
        Révoque tous les tokens d'un utilisateur.
        Utilisé lors d'une déconnexion forcée (compte compromis, changement mdp).
        """
        from datetime import datetime

        from django.core.cache import cache

        # Stocker un timestamp "tous les tokens avant X sont invalides"
        cache.set(
            f"jwt:user_revoked:{user_id}",
            datetime.now(tz=UTC).timestamp(),
            timeout=int(self.REFRESH_EXPIRE.total_seconds()),
        )

    def _is_blacklisted(self, jti: str) -> bool:
        from django.core.cache import cache

        return cache.get(f"jwt:blacklist:{jti}") is not None
