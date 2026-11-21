"""Tests du service d'authentification, de l'authentification JWT DRF et des adapters SMS."""

import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.application.services.auth_service import AuthService
from core.exceptions.base import (
    BusinessRuleViolationException,
    ExternalServiceException,
    ValidationException,
)

pytestmark = pytest.mark.django_db

STRONG = "Nouveau#Pass2026"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="auth@test.sn", telephone="+221772222222", password="Ancien#Pass2026", nom="Moussa Faye"
    )


@pytest.fixture
def deps():
    return {
        "user_repo": MagicMock(),
        "jwt_service": MagicMock(),
        "otp_service": MagicMock(),
        "sms_service": MagicMock(),
        "audit_service": MagicMock(),
    }


@pytest.fixture
def service(deps):
    return AuthService(**deps)


class TestChangePassword:
    def test_succes_revoque_les_tokens(self, service, deps):
        deps["user_repo"].check_password.return_value = True
        assert service.change_password("u1", "Ancien#Pass2026", STRONG) is True
        deps["user_repo"].set_password.assert_called_once_with("u1", STRONG)
        deps["jwt_service"].revoke_all_for_user.assert_called_once_with("u1")

    def test_ancien_mot_de_passe_incorrect(self, service, deps):
        deps["user_repo"].check_password.return_value = False
        with pytest.raises(BusinessRuleViolationException):
            service.change_password("u1", "faux", STRONG)

    @pytest.mark.parametrize(
        "weak",
        ["Court#1", "minuscule#pass2026", "MAJUSCULE#PASS2026", "SansChiffre#Pass", "SansSpecial2026Pass"],
    )
    def test_mot_de_passe_faible(self, service, deps, weak):
        deps["user_repo"].check_password.return_value = True
        with pytest.raises(ValidationException):
            service.change_password("u1", "Ancien#Pass2026", weak)

    def test_identique_a_l_ancien(self, service, deps):
        deps["user_repo"].check_password.return_value = True
        with pytest.raises(ValidationException):
            service.change_password("u1", STRONG, STRONG)


class TestDeuxFacteurs:
    def test_activation_envoie_un_sms(self, service, deps):
        deps["otp_service"].generate.return_value = "123456"
        deps["user_repo"].get_by_id.return_value = SimpleNamespace(telephone="+221772222222")
        assert "SMS" in service.enable_2fa("u1", "+221772222222")["message"]
        assert "123456" in deps["sms_service"].send.call_args.kwargs["message"]

    def test_confirmation(self, service, deps, user):
        deps["otp_service"].verify.return_value = True
        assert service.confirm_2fa(str(user.id), "123456") is True
        user.refresh_from_db()
        assert user.is_2fa_enabled is True

    def test_confirmation_code_faux(self, service, deps):
        deps["otp_service"].verify.return_value = False
        assert service.confirm_2fa("u1", "000000") is False

    def test_desactivation(self, service, deps, user):
        user.is_2fa_enabled = True
        user.save()
        deps["user_repo"].check_password.return_value = True
        assert service.disable_2fa(str(user.id), "x") is True
        user.refresh_from_db()
        assert user.is_2fa_enabled is False

    def test_desactivation_mot_de_passe_faux(self, service, deps):
        deps["user_repo"].check_password.return_value = False
        with pytest.raises(BusinessRuleViolationException):
            service.disable_2fa("u1", "faux")


class TestLogout:
    def test_sans_refresh(self, service, deps):
        service.logout("u1", "jti-access")
        deps["jwt_service"].revoke.assert_called_once_with("jti-access")

    def test_avec_refresh(self, service, deps):
        with patch("apps.users.application.services.jwt_service.JWTService") as jwt_cls:
            jwt_cls.return_value.validate_refresh.return_value = {"jti": "jti-refresh"}
            service.logout("u1", "jti-access", refresh_token="refresh")
        deps["jwt_service"].revoke.assert_any_call("jti-refresh", ttl=7 * 24 * 3600)


class TestVerrouillage:
    def test_verrouille_apres_cinq_echecs(self, service, deps, user):
        for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
            service.handle_failed_login(str(user.id))
        user.refresh_from_db()
        assert user.failed_attempts == 5
        assert user.locked_until is not None
        deps["sms_service"].send.assert_called()
        assert service.is_account_locked(str(user.id)) is True

    def test_echec_sms_ne_bloque_pas(self, service, deps, user):
        deps["sms_service"].send.side_effect = RuntimeError("SMS indisponible")
        for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
            service.handle_failed_login(str(user.id))
        user.refresh_from_db()
        assert user.locked_until is not None

    def test_utilisateur_inexistant(self, service):
        service.handle_failed_login(str(uuid.uuid4()))
        assert service.is_account_locked(str(uuid.uuid4())) is False

    def test_deverrouillage_automatique(self, service, user):
        user.locked_until = timezone.now() - timedelta(minutes=1)
        user.failed_attempts = 5
        user.save()
        assert service.is_account_locked(str(user.id)) is False
        user.refresh_from_db()
        assert user.locked_until is None
        assert user.failed_attempts == 0

    def test_reset(self, service, user):
        user.failed_attempts = 3
        user.save()
        service.reset_failed_attempts(str(user.id))
        user.refresh_from_db()
        assert user.failed_attempts == 0


class TestJWTServiceAuthentication:
    def _auth(self, header=None):
        from core.authentication.jwt_auth import JWTServiceAuthentication

        factory = APIRequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION=header) if header else factory.get("/")
        return JWTServiceAuthentication().authenticate(request)

    def _token(self, sub):
        token = AccessToken()
        token["sub"] = str(sub)
        return str(token)

    def test_sans_entete(self):
        assert self._auth() is None

    def test_entete_mal_forme(self):
        assert self._auth("Token abc") is None

    def test_token_valide(self, user):
        authenticated, _ = self._auth(f"Bearer {self._token(user.id)}")
        assert authenticated == user

    def test_token_invalide(self):
        with pytest.raises(AuthenticationFailed):
            self._auth("Bearer pas-un-jwt")

    def test_token_revoque(self, user):
        raw = self._token(user.id)
        cache.set(f"jwt:blacklist:{AccessToken(raw)['jti']}", 1)
        with pytest.raises(AuthenticationFailed, match="révoqué"):
            self._auth(f"Bearer {raw}")

    def test_utilisateur_introuvable(self):
        with pytest.raises(AuthenticationFailed, match="introuvable"):
            self._auth(f"Bearer {self._token(uuid.uuid4())}")

    def test_compte_desactive(self, user):
        user.is_active = False
        user.save()
        with pytest.raises(AuthenticationFailed, match="désactivé"):
            self._auth(f"Bearer {self._token(user.id)}")

    def test_entete_www_authenticate(self):
        from core.authentication.jwt_auth import JWTServiceAuthentication

        assert JWTServiceAuthentication().authenticate_header(None).startswith("Bearer")


class TestSMSAdapters:
    def test_twilio(self):
        from apps.users.infrastructure.adapters.sms_adapter import TwilioSMSAdapter

        with patch("twilio.rest.Client") as client_cls:
            client_cls.return_value.messages.create.return_value = SimpleNamespace(sid="SM1")
            adapter = TwilioSMSAdapter("sid", "token", "+15550000000")
            assert adapter.send("+221770000000", "Bonjour") is True
            client_cls.return_value.messages.create.side_effect = RuntimeError("quota")
            with pytest.raises(ExternalServiceException):
                adapter.send("+221770000000", "Bonjour")

    def test_orange_sms(self):
        from apps.users.infrastructure.adapters.sms_adapter import OrangeSMSSenegalAdapter

        adapter = OrangeSMSSenegalAdapter("key", "+221330000000")
        with patch("requests.post") as post:
            assert adapter.send("+221770000000", "Bonjour") is True
            assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer key"
            post.side_effect = RuntimeError("down")
            with pytest.raises(ExternalServiceException):
                adapter.send("+221770000000", "Bonjour")

    @override_settings(DEBUG=False, SMS_PROVIDER="twilio", TWILIO_ACCOUNT_SID=None)
    def test_factory_twilio_non_configure(self):
        from apps.users.infrastructure.adapters.sms_adapter import ConsoleSMSAdapter, get_sms_adapter

        assert isinstance(get_sms_adapter(), ConsoleSMSAdapter)

    @override_settings(
        DEBUG=False,
        SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="sid",
        TWILIO_AUTH_TOKEN="tok",
        TWILIO_FROM_NUMBER="+1555",
    )
    def test_factory_twilio(self):
        from apps.users.infrastructure.adapters.sms_adapter import TwilioSMSAdapter, get_sms_adapter

        with patch("twilio.rest.Client"):
            assert isinstance(get_sms_adapter(), TwilioSMSAdapter)

    @override_settings(DEBUG=False, SMS_PROVIDER="orange", ORANGE_SMS_API_KEY="k", ORANGE_SMS_SENDER_ID="s")
    def test_factory_orange(self):
        from apps.users.infrastructure.adapters.sms_adapter import OrangeSMSSenegalAdapter, get_sms_adapter

        assert isinstance(get_sms_adapter(), OrangeSMSSenegalAdapter)

    @override_settings(DEBUG=False, SMS_PROVIDER="pigeon")
    def test_factory_inconnu(self):
        from apps.users.infrastructure.adapters.sms_adapter import get_sms_adapter

        with pytest.raises(ValueError):
            get_sms_adapter()

    @override_settings(DEBUG=True)
    def test_factory_debug(self):
        from apps.users.infrastructure.adapters.sms_adapter import ConsoleSMSAdapter, get_sms_adapter

        adapter = get_sms_adapter()
        assert isinstance(adapter, ConsoleSMSAdapter)
        assert adapter.send("+221770000000", "test") is True
