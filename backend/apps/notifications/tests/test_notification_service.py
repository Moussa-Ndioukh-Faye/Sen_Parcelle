"""
apps/notifications/tests/test_notification_service.py
─────────────────────────────────────────────────────────
Tests pour NotificationService.
"""

from unittest.mock import Mock

from django.test import TestCase

from apps.notifications.services.notification_service import NotificationService


class TestNotificationService(TestCase):
    """Tests du service de notifications."""

    def setUp(self):
        self.mock_sms_adapter = Mock()
        self.service = NotificationService(sms_adapter=self.mock_sms_adapter)

    def test_notify_parcel_submitted(self):
        """Test de notification de soumission."""
        user = Mock()
        user.email = "test@example.com"
        user.telephone = "+221123456789"

        parcel = Mock()
        parcel.id = "12345678-1234-5678-1234-567812345678"

        self.service.notify_parcel_submitted(user, parcel)

        # Vérifie que le SMS a été envoyé
        self.mock_sms_adapter.send.assert_called_once()
        call_args = self.mock_sms_adapter.send.call_args
        assert "+221123456789" in call_args[0]

    def test_notify_payment_confirmed(self):
        """Test de notification de paiement confirmé."""
        user = Mock()
        user.email = "test@example.com"
        user.telephone = "+221123456789"

        transaction = Mock()
        transaction.id = "tx-123"
        transaction.amount = 5000000

        self.service.notify_payment_confirmed(user, transaction)

        self.mock_sms_adapter.send.assert_called_once()

    def test_notify_kyc_approved(self):
        """Test de notification KYC approuvé."""
        user = Mock()
        user.email = "test@example.com"
        user.telephone = "+221123456789"

        self.service.notify_kyc_approved(user)

        self.mock_sms_adapter.send.assert_called_once()
        call_args = self.mock_sms_adapter.send.call_args
        assert "approuvé" in call_args[0][1]

    def test_notify_kyc_rejected(self):
        """Test de notification KYC rejeté."""
        user = Mock()
        user.email = "test@example.com"
        user.telephone = "+221123456789"

        self.service.notify_kyc_rejected(user, "Documents illisibles")

        self.mock_sms_adapter.send.assert_called_once()
        call_args = self.mock_sms_adapter.send.call_args
        assert "rejeté" in call_args[0][1]

    def test_without_sms_adapter(self):
        """Test sans adaptateur SMS (notifications simulées)."""
        service = NotificationService()  # Pas d'adaptateur

        user = Mock()
        user.email = "test@example.com"
        user.telephone = "+221123456789"

        parcel = Mock()
        parcel.id = "123"

        # Ne doit pas lever d'exception
        service.notify_parcel_submitted(user, parcel)
        service.notify_parcel_validated(user, parcel)
