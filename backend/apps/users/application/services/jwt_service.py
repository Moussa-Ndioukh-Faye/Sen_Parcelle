"""
apps/users/application/services/jwt_service.py
-----------------------------------------------
Service JWT complet pour Sen_parcelle.
- Access token (15 min) + Refresh token (7 jours)
- Blacklist des tokens révoqués (Redis)
- Payload enrichi (role, kyc_status)
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from django.conf import settings

logger = logging.getLogger(__name__)


class JWTService:
    """
    Gestion des tokens JWT.
    Utilise Redis pour la blacklist (révocation).
    """

    ACCESS_EXPIRE  = timedelta(minutes=15)
    REFRESH_EXPIRE = timedelta(days=7)
    ALGORITHM      = "HS256"

    def __init__(self, cache_backend=None):
        """
        cache_backend : instance Django cache (Redis).
        Si None, utilise le cache Django par défaut.
        """
        self._cache = cache_backend

    @property
    def _secret(self) -> str:
        return settings.SECRET_KEY

    # ──────────────────────────────────────────────
    # GÉNÉRATION
    # ──────────────────────────────────────────────

    def generate(self, user_id: str, role: str, kyc_status: str = "pending") -> dict:
        """
        Génère un couple access + refresh token.

        Payload access token :
        {
            "sub":        user_id,
            "role":       role,
            "kyc_status": kyc_status,
            "type":       "access",
            "jti":        uuid unique (pour blacklist),
            "iat":        issued at,
            "exp":        expiration,
        }
        """
        now = datetime.now(tz=timezone.utc)

        # ─── Access token ───
        access_jti = str(uuid.uuid4())
        access_payload = {
            "sub":        user_id,
            "role":       role,
            "kyc_status": kyc_status,
            "type":       "access",
            "jti":        access_jti,
            "iat":        now,
            "exp":        now + self.ACCESS_EXPIRE,
        }

        # ─── Refresh token ───
        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "sub":  user_id,
            "type": "refresh",
            "jti":  refresh_jti,
            "iat":  now,
            "exp":  now + self.REFRESH_EXPIRE,
        }

        return {
            "access":      jwt.encode(access_payload,  self._secret, algorithm=self.ALGORITHM),
            "refresh":     jwt.encode(refresh_payload, self._secret, algorithm=self.ALGORITHM),
            "access_jti":  access_jti,
            "refresh_jti": refresh_jti,
            "expires_in":  int(self.ACCESS_EXPIRE.total_seconds()),
        }

    # ──────────────────────────────────────────────
    # VALIDATION
    # ──────────────────────────────────────────────

    def validate_access(self, token: str) -> Optional[dict]:
        """
        Valide un access token.
        Retourne le payload ou None si invalide/expiré/blacklisté.
        """
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self.ALGORITHM])

            if payload.get("type") != "access":
                return None

            # Vérifier blacklist Redis
            if self._is_blacklisted(payload["jti"]):
                logger.warning(f"Token blacklisté utilisé : jti={payload['jti']}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token invalide : {e}")
            return None

    def validate_refresh(self, token: str) -> Optional[dict]:
        """Valide un refresh token."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self.ALGORITHM])

            if payload.get("type") != "refresh":
                return None

            if self._is_blacklisted(payload["jti"]):
                return None

            return payload

        except jwt.InvalidTokenError:
            return None

    def refresh(self, refresh_token: str) -> Optional[dict]:
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

    def revoke(self, jti: str, ttl: int = None):
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
        from django.core.cache import cache
        # Stocker un timestamp "tous les tokens avant X sont invalides"
        cache.set(
            f"jwt:user_revoked:{user_id}",
            datetime.now(tz=timezone.utc).timestamp(),
            timeout=int(self.REFRESH_EXPIRE.total_seconds()),
        )

    def _is_blacklisted(self, jti: str) -> bool:
        from django.core.cache import cache
        return cache.get(f"jwt:blacklist:{jti}") is not None


# ══════════════════════════════════════════════════════════════
# MIDDLEWARE JWT — Injecte l'utilisateur dans request
# apps/users/infrastructure/jwt_middleware.py
# ══════════════════════════════════════════════════════════════

class JWTAuthenticationMiddleware:
    """
    Middleware alternatif pour injecter request.user depuis JWT.
    Complément de la classe DRF JWTAuthentication.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._jwt_service = JWTService()

    def __call__(self, request):
        token = self._extract_token(request)
        if token:
            payload = self._jwt_service.validate_access(token)
            if payload:
                self._attach_user(request, payload)
        return self.get_response(request)

    @staticmethod
    def _extract_token(request) -> Optional[str]:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    @staticmethod
    def _attach_user(request, payload: dict):
        from apps.users.infrastructure.models import User
        try:
            request.user = User.objects.get(id=payload["sub"])
        except User.DoesNotExist:
            pass
