"""
tests/test_security.py
-----------------------
Tests unitaires pour tous les composants de sécurité.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta


# ══════════════════════════════════════════════════════════════
# TESTS JWT
# ══════════════════════════════════════════════════════════════

class TestJWTService:

    @pytest.fixture
    def jwt_service(self):
        from apps.users.application.services.jwt_service import JWTService
        svc = JWTService()
        return svc

    @pytest.fixture(autouse=True)
    def mock_django_settings(self, settings):
        settings.SECRET_KEY = "test-secret-key-pour-les-tests"

    def test_generate_retourne_access_et_refresh(self, jwt_service):
        tokens = jwt_service.generate("user-123", "acheteur", "verified")
        assert "access"  in tokens
        assert "refresh" in tokens
        assert tokens["access"]  != ""
        assert tokens["refresh"] != ""

    def test_access_token_valide(self, jwt_service):
        tokens  = jwt_service.generate("user-123", "acheteur")
        payload = jwt_service.validate_access(tokens["access"])
        assert payload is not None
        assert payload["sub"]  == "user-123"
        assert payload["role"] == "acheteur"
        assert payload["type"] == "access"

    def test_refresh_token_invalide_comme_access(self, jwt_service):
        tokens = jwt_service.generate("user-123", "acheteur")
        # Utiliser le refresh comme access → refusé
        payload = jwt_service.validate_access(tokens["refresh"])
        assert payload is None

    def test_token_expire(self, jwt_service):
        import jwt
        import time
        # Créer un token déjà expiré
        payload = {
            "sub": "user-123", "type": "access",
            "jti": "test-jti", "role": "acheteur",
            "iat": time.time() - 100,
            "exp": time.time() - 10,  # Expiré il y a 10s
        }
        expired_token = jwt.encode(payload, "test-secret-key-pour-les-tests", algorithm="HS256")
        result = jwt_service.validate_access(expired_token)
        assert result is None

    @patch("django.core.cache.cache")
    def test_token_blackliste_est_rejete(self, mock_cache, jwt_service):
        mock_cache.get.return_value = "1"  # Token en blacklist
        tokens  = jwt_service.generate("user-123", "acheteur")
        payload = jwt_service.validate_access(tokens["access"])
        assert payload is None

    def test_token_invalide_signature(self, jwt_service):
        import jwt
        # Signer avec une autre clé
        payload = {
            "sub": "user-123", "type": "access",
            "jti": "test-jti", "role": "acheteur",
        }
        bad_token = jwt.encode(payload, "mauvaise-cle", algorithm="HS256")
        result = jwt_service.validate_access(bad_token)
        assert result is None


# ══════════════════════════════════════════════════════════════
# TESTS OTP
# ══════════════════════════════════════════════════════════════

class TestOTPService:

    @pytest.fixture
    def otp_service(self):
        from apps.users.application.services.otp_service import OTPService
        return OTPService()

    @patch("django.core.cache.cache")
    def test_generate_produit_code_6_chiffres(self, mock_cache, otp_service):
        mock_cache.set = MagicMock()
        code = otp_service.generate("user-123", "login")
        assert len(code) == 6
        assert code.isdigit()

    @patch("django.core.cache.cache")
    def test_verify_code_correct(self, mock_cache, otp_service):
        mock_cache.get.side_effect = lambda key, *args, **kwargs: (
            "123456" if "code" in key else 0
        )
        mock_cache.incr.return_value = 1
        mock_cache.delete = MagicMock()
        result = otp_service.verify("user-123", "123456", "login")
        assert result is True

    @patch("django.core.cache.cache")
    def test_verify_code_incorrect_leve_exception(self, mock_cache, otp_service):
        from core.exceptions.base import InvalidOTPException
        mock_cache.get.side_effect = lambda key, *args, **kwargs: (
            "123456" if "code" in key else 0
        )
        mock_cache.incr.return_value = 1
        mock_cache.set = MagicMock()

        with pytest.raises(InvalidOTPException):
            otp_service.verify("user-123", "999999", "login")

    @patch("django.core.cache.cache")
    def test_verify_code_expire_leve_exception(self, mock_cache, otp_service):
        from core.exceptions.base import InvalidOTPException
        mock_cache.get.return_value = None  # Code expiré (TTL Redis)

        with pytest.raises(InvalidOTPException):
            otp_service.verify("user-123", "123456", "login")

    @patch("django.core.cache.cache")
    def test_trop_de_tentatives_bloque(self, mock_cache, otp_service):
        from core.exceptions.base import BusinessRuleViolationException
        mock_cache.get.side_effect = lambda key, *args, **kwargs: (
            "123456" if "code" in key else 5   # 5 tentatives = bloqué
        )
        mock_cache.incr.return_value = 5
        mock_cache.delete = MagicMock()

        with pytest.raises(BusinessRuleViolationException) as exc_info:
            otp_service.verify("user-123", "000000", "login")
        assert "tentatives" in exc_info.value.message.lower()

    @patch("django.core.cache.cache")
    def test_usage_unique_code_invalide_apres_verification(self, mock_cache, otp_service):
        """Un OTP ne peut être utilisé qu'une seule fois."""
        call_count = {"n": 0}

        def mock_get(key, *args, **kwargs):
            if "code" in key:
                # Retourne None au 2ème appel (code supprimé après usage)
                if call_count["n"] == 0:
                    call_count["n"] += 1
                    return "123456"
                return None
            return 0

        mock_cache.get.side_effect = mock_get
        mock_cache.incr.return_value = 1
        mock_cache.delete          = MagicMock()
        mock_cache.set             = MagicMock()

        # Premier usage → valide
        result = otp_service.verify("user-123", "123456", "login")
        assert result is True

        # Deuxième usage → expiré
        from core.exceptions.base import InvalidOTPException
        with pytest.raises(InvalidOTPException):
            otp_service.verify("user-123", "123456", "login")


# ══════════════════════════════════════════════════════════════
# TESTS CRYPTO
# ══════════════════════════════════════════════════════════════

class TestCryptoService:

    def test_hash_document_sha256(self):
        from core.utils.crypto import CryptoService
        content = b"Titre foncier Almadies"
        h       = CryptoService.hash_document(content)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_document_deterministe(self):
        from core.utils.crypto import CryptoService
        content = b"Document test"
        assert CryptoService.hash_document(content) == CryptoService.hash_document(content)

    def test_hash_document_different_si_contenu_different(self):
        from core.utils.crypto import CryptoService
        assert CryptoService.hash_document(b"doc1") != CryptoService.hash_document(b"doc2")

    def test_verify_document_hash_valide(self):
        from core.utils.crypto import CryptoService
        content = b"Titre foncier test"
        h       = CryptoService.hash_document(content)
        assert CryptoService.verify_document_hash(content, h) is True

    def test_verify_document_hash_invalide(self):
        from core.utils.crypto import CryptoService
        assert CryptoService.verify_document_hash(b"contenu", "a" * 64) is False

    def test_mask_phone(self):
        from core.utils.crypto import CryptoService
        masked = CryptoService.mask_phone("+221776543210")
        assert "***" in masked
        assert not masked.startswith("+221776")  # Masqué

    def test_mask_email(self):
        from core.utils.crypto import CryptoService
        masked = CryptoService.mask_email("moussa@email.com")
        assert "***" in masked
        assert "@email.com" in masked


# ══════════════════════════════════════════════════════════════
# TESTS VALIDATORS SÉNÉGAL
# ══════════════════════════════════════════════════════════════

class TestSenegalValidators:

    def test_phone_valide_77(self):
        from core.utils.crypto import SenegalValidators
        ok, normalized = SenegalValidators.validate_phone("776543210")
        assert ok is True
        assert normalized == "+221776543210"

    def test_phone_valide_avec_indicatif(self):
        from core.utils.crypto import SenegalValidators
        ok, normalized = SenegalValidators.validate_phone("+221776543210")
        assert ok is True

    def test_phone_invalide_mauvais_prefixe(self):
        from core.utils.crypto import SenegalValidators
        ok, _ = SenegalValidators.validate_phone("556543210")
        assert ok is False

    def test_price_valide(self):
        from core.utils.crypto import SenegalValidators
        ok, _ = SenegalValidators.validate_price(25_000_000)
        assert ok is True

    def test_price_trop_basse(self):
        from core.utils.crypto import SenegalValidators
        ok, msg = SenegalValidators.validate_price(50_000)
        assert ok is False
        assert "100 000" in msg

    def test_region_valide(self):
        from core.utils.crypto import SenegalValidators
        assert SenegalValidators.validate_region("Dakar") is True
        assert SenegalValidators.validate_region("Paris") is False


# ══════════════════════════════════════════════════════════════
# TESTS RATE LIMITING
# ══════════════════════════════════════════════════════════════

class TestRateLimitService:

    @patch("django.core.cache.cache")
    def test_premiere_requete_autorisee(self, mock_cache):
        from core.utils.crypto import RateLimitService
        mock_cache.get.return_value = []
        mock_cache.set = MagicMock()
        svc = RateLimitService()
        allowed, remaining = svc.is_allowed("test:key", max_requests=5, window_seconds=60)
        assert allowed is True
        assert remaining == 4

    @patch("django.core.cache.cache")
    def test_limite_atteinte_bloque(self, mock_cache):
        import time
        from core.utils.crypto import RateLimitService
        # Simuler 5 requêtes récentes
        now = time.time()
        mock_cache.get.return_value = [now - i for i in range(5)]
        svc = RateLimitService()
        allowed, remaining = svc.is_allowed("test:key", max_requests=5, window_seconds=60)
        assert allowed   is False
        assert remaining == 0
