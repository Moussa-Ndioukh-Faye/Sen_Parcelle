"""
core/authentication/jwt_auth.py
--------------------------------
Authentification DRF personnalisée qui valide le token via SimpleJWT
et vérifie la blacklist Redis du JWTService.
"""

import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)


class JWTServiceAuthentication(BaseAuthentication):
    """
    Validation JWT :
    1. Signature + expiry via SimpleJWT (AccessToken)
    2. Blacklist Redis via JWTService
    """

    www_authenticate_realm = "api"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth:
            return None

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        raw_token = parts[1]

        try:
            # 1. Validation SimpleJWT
            access_token = AccessToken(raw_token)
            payload = {k: access_token[k] for k in access_token.payload}

            # 2. Vérification blacklist Redis
            jti = payload.get("jti")
            if jti and self._is_blacklisted(jti):
                raise AuthenticationFailed("Token révoqué.")

            # 3. Récupérer l'utilisateur
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=payload["sub"])
            except User.DoesNotExist:
                raise AuthenticationFailed("Utilisateur introuvable.")

            if not user.is_active:
                raise AuthenticationFailed("Compte désactivé.")

            return (user, access_token)

        except TokenError as e:
            raise AuthenticationFailed(
                f"Token invalide : {e}"
            ) from e

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'

    def _is_blacklisted(self, jti: str) -> bool:
        from django.core.cache import cache
        return cache.get(f"jwt:blacklist:{jti}") is not None
