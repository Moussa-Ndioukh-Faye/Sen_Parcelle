"""
core/security/
--------------
Sécurité avancée : rate limiting, validators, crypto helpers.
"""

import contextlib
import hashlib
import hmac
import logging
import re

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# CRYPTO HELPERS
# core/utils/crypto.py
# ══════════════════════════════════════════════════════════════


class CryptoService:
    """Utilitaires cryptographiques pour Sen_parcelle."""

    @staticmethod
    def hash_document(content: bytes) -> str:
        """
        Hash SHA-256 d'un document.
        Utilisé avant upload S3 + enregistrement blockchain.
        """
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def verify_document_hash(content: bytes, expected_hash: str) -> bool:
        """Vérifie l'intégrité d'un document par son hash."""
        actual = CryptoService.hash_document(content)
        return hmac.compare_digest(actual, expected_hash)

    @staticmethod
    def hash_password_check(password: str, hashed: str) -> bool:
        """
        Vérifie un mot de passe bcrypt.
        Délégué à Django (set_password / check_password).
        """
        from django.contrib.auth.hashers import check_password

        return check_password(password, hashed)

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Génère un token aléatoire sécurisé (pour les URLs de reset)."""
        import secrets

        return secrets.token_urlsafe(length)

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Masque un numéro de téléphone pour les logs : +221***210."""
        if len(phone) < 6:
            return "***"
        return phone[:4] + "***" + phone[-3:]

    @staticmethod
    def mask_email(email: str) -> str:
        """Masque un email pour les logs : m***a@email.com."""
        parts = email.split("@")
        if len(parts) != 2:
            return "***"
        local = parts[0]
        masked = local[0] + "***" + (local[-1] if len(local) > 1 else "")
        return f"{masked}@{parts[1]}"


# ══════════════════════════════════════════════════════════════
# VALIDATORS SÉNÉGAL
# core/validators.py
# ══════════════════════════════════════════════════════════════


class SenegalValidators:
    """Validators spécifiques au contexte sénégalais."""

    # Préfixes valides opérateurs SN
    VALID_PHONE_PREFIXES = ("70", "75", "76", "77", "78")

    @classmethod
    def validate_phone(cls, phone: str) -> tuple[bool, str]:
        """
        Valide un numéro sénégalais.
        Retourne (is_valid, normalized_number).
        """
        digits = re.sub(r"\D", "", phone)

        # Retirer indicatif 221
        if digits.startswith("221"):
            digits = digits[3:]

        if len(digits) != 9:
            return False, ""

        if not any(digits.startswith(p) for p in cls.VALID_PHONE_PREFIXES):
            return False, ""

        return True, f"+221{digits}"

    @staticmethod
    def validate_cni(cni: str) -> bool:
        """
        Valide un numéro CNI sénégalais.
        Format : 1 lettre + 10 chiffres (ex: B12345678901).
        """
        pattern = r"^[A-Z]\d{10}$"
        return bool(re.match(pattern, cni.strip().upper()))

    @staticmethod
    def validate_prix(prix: float) -> tuple[bool, str]:
        """Prix en FCFA : entre 100 000 et 10 milliards."""
        if prix < 100_000:
            return False, "Prix minimum : 100 000 FCFA"
        if prix > 10_000_000_000:
            return False, "Prix maximum : 10 milliards FCFA"
        return True, ""

    @staticmethod
    def validate_superficie(superficie_m2: float) -> tuple[bool, str]:
        """Superficie en m² : entre 10 et 100 000 m²."""
        if superficie_m2 < 10:
            return False, "Superficie minimum : 10 m²"
        if superficie_m2 > 100_000:
            return False, "Superficie maximum : 100 000 m²"

        return True, ""

    SENEGAL_REGIONS = {
        "Dakar",
        "Thiès",
        "Saint-Louis",
        "Ziguinchor",
        "Kaolack",
        "Diourbel",
        "Louga",
        "Fatick",
        "Kolda",
        "Tambacounda",
        "Kaffrine",
        "Matam",
        "Kédougou",
        "Sédhiou",
    }

    @classmethod
    def validate_region(cls, region: str) -> bool:
        return region in cls.SENEGAL_REGIONS


# ══════════════════════════════════════════════════════════════
# SECURITY HEADERS MIDDLEWARE
# core/security/headers_middleware.py
# ══════════════════════════════════════════════════════════════


class SecurityHeadersMiddleware:
    """
    Ajoute des headers de sécurité à toutes les réponses.
    Protège contre XSS, clickjacking, MIME sniffing, etc.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ─── Headers de sécurité ───
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://polygon-mainnet.g.alchemy.com; "
            "frame-ancestors 'none';"
        )

        # ─── Supprimer les headers qui révèlent la stack ───
        for header in ("Server", "X-Powered-By", "X-Django-Version"):
            with contextlib.suppress(KeyError, AttributeError):
                del response[header]

        return response


# ══════════════════════════════════════════════════════════════
# RATE LIMITING CUSTOM (complément django-ratelimit)
# core/security/rate_limit.py
# ══════════════════════════════════════════════════════════════


class RateLimitService:
    """
    Rate limiting Redis avec fenêtre glissante.
    Plus précis que le rate limiting par minute fixe.
    """

    def __init__(self):
        from django.core.cache import cache

        self._cache = cache

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Vérifie si une action est autorisée.
        Retourne (allowed, remaining_requests).

        Algorithme : fenêtre glissante avec timestamps.
        """
        import time

        now = time.time()
        window_key = f"rl:{key}"

        # Récupérer les timestamps existants
        timestamps = self._cache.get(window_key) or []

        # Nettoyer les timestamps hors de la fenêtre
        cutoff = now - window_seconds
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= max_requests:
            return False, 0

        # Ajouter le timestamp actuel
        timestamps.append(now)
        self._cache.set(window_key, timestamps, timeout=window_seconds)

        return True, max_requests - len(timestamps)

    def check_login(self, ip: str) -> tuple[bool, int]:
        """5 tentatives de connexion par IP par 15 minutes."""
        return self.is_allowed(f"login:{ip}", max_requests=5, window_seconds=900)

    def check_otp(self, user_id: str) -> tuple[bool, int]:
        """3 demandes OTP par utilisateur par 10 minutes."""
        return self.is_allowed(f"otp:{user_id}", max_requests=3, window_seconds=600)

    def check_api(self, user_id: str) -> tuple[bool, int]:
        """1000 requêtes API par utilisateur par heure."""
        return self.is_allowed(f"api:{user_id}", max_requests=1000, window_seconds=3600)
