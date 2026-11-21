"""Tests des tâches Celery de notification (SMS, push Firebase, rapport quotidien)."""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail

from apps.notifications.tasks import send_daily_admin_report, send_push_notification, send_sms_async

pytestmark = pytest.mark.django_db


class TestSendSMS:
    def test_envoi(self):
        adapter = MagicMock()
        with patch("apps.users.infrastructure.adapters.sms_adapter.get_sms_adapter", return_value=adapter):
            send_sms_async("+221770000000", "Bonjour")
        adapter.send.assert_called_once_with(to="+221770000000", message="Bonjour")

    def test_erreur_absorbee(self):
        adapter = MagicMock()
        adapter.send.side_effect = RuntimeError("SMS indisponible")
        with patch("apps.users.infrastructure.adapters.sms_adapter.get_sms_adapter", return_value=adapter):
            send_sms_async("+221770000000", "Bonjour")  # ne lève pas


@pytest.fixture
def firebase():
    """Module firebase_admin factice : la tâche l'importe à l'exécution."""
    firebase_admin = ModuleType("firebase_admin")
    firebase_admin.get_app = MagicMock()
    firebase_admin.initialize_app = MagicMock()
    credentials = ModuleType("firebase_admin.credentials")
    credentials.Certificate = MagicMock()
    messaging = ModuleType("firebase_admin.messaging")
    messaging.Message = MagicMock()
    messaging.Notification = MagicMock()
    messaging.send = MagicMock(return_value="projects/x/messages/1")
    firebase_admin.credentials = credentials
    firebase_admin.messaging = messaging
    modules = {
        "firebase_admin": firebase_admin,
        "firebase_admin.credentials": credentials,
        "firebase_admin.messaging": messaging,
    }
    with patch.dict(sys.modules, modules):
        yield firebase_admin


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="push@test.sn", telephone="+221773333333", password="x", nom="Push Test"
    )


class TestSendPush:
    @pytest.fixture(autouse=True)
    def _settings(self, settings):
        settings.FIREBASE_SERVICE_ACCOUNT_JSON = "/tmp/firebase.json"

    def test_envoi_avec_token(self, firebase, user):
        with patch("apps.users.infrastructure.models.User.objects") as objects:
            objects.get.return_value = SimpleNamespace(fcm_token="token-fcm")
            send_push_notification(str(user.id), "Titre", "Message", {"k": "v"})
        firebase.messaging.send.assert_called_once()
        assert firebase.messaging.Message.call_args.kwargs["token"] == "token-fcm"

    def test_sans_token(self, firebase, user):
        send_push_notification(str(user.id), "Titre", "Message")
        firebase.messaging.send.assert_not_called()

    def test_initialise_firebase_si_necessaire(self, firebase, user):
        firebase.get_app.side_effect = ValueError("pas d'app")
        send_push_notification(str(user.id), "Titre", "Message")
        firebase.initialize_app.assert_called_once()

    def test_erreur_absorbee(self, firebase):
        send_push_notification("inexistant", "Titre", "Message")  # ne lève pas


class TestDailyReport:
    @pytest.fixture(autouse=True)
    def _settings(self, settings):
        settings.FRONTEND_URL = "https://admin.sen-parcelle.sn"
        settings.DEFAULT_FROM_EMAIL = "noreply@sen-parcelle.sn"
        settings.ADMINS = [("Admin", "admin@sen-parcelle.sn")]
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def test_envoie_le_rapport(self, user):
        send_daily_admin_report()
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ["admin@sen-parcelle.sn"]
        assert "Nouveaux utilisateurs : 1" in message.body
        assert "https://admin.sen-parcelle.sn/admin" in message.body
