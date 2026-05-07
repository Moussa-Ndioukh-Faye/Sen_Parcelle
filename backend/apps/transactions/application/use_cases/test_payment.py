"""
apps/transactions/application/use_cases/test_payment.py
─────────────────────────────────────────────────────────
Tests pour InitiatePaymentUseCase et ConfirmPaymentUseCase.
"""

from unittest.mock import Mock, patch
from django.test import TestCase


class TestInitiatePaymentUseCase(TestCase):
    """Tests du use case d'initiation de paiement."""

    def setUp(self):
        self.mock_parcel_repo = Mock()
        self.mock_user_repo = Mock()
        self.mock_tx_repo = Mock()
        self.mock_payment_factory = Mock()
        self.mock_notif = Mock()
        self.mock_audit = Mock()

        from apps.transactions.application.use_cases.payment import InitiatePaymentUseCase
        self.uc = InitiatePaymentUseCase(
            parcel_repo=self.mock_parcel_repo,
            user_repo=self.mock_user_repo,
            tx_repo=self.mock_tx_repo,
            payment_factory=self.mock_payment_factory,
            notification_service=self.mock_notif,
            audit_service=self.mock_audit,
        )

    @patch('apps.transactions.application.use_cases.payment.ValidateParcelUseCase')
    def test_initiate_payment_success(self, mock_validate_uc):
        """Test d'initiation réussie."""
        # Mock parcelle certifiée
        mock_parcel = Mock()
        mock_parcel.is_certified = True
        mock_parcel.owner_id = 'seller-123'
        mock_parcel.price = 5000000
        self.mock_parcel_repo.get_by_id.return_value = mock_parcel

        # Mock acheteur avec KYC
        mock_buyer = Mock()
        mock_buyer.is_kyc_verified = True
        mock_buyer.is_2fa_enabled = True
        self.mock_user_repo.get_by_id.return_value = mock_buyer

        # Mock payment adapter
        mock_adapter = Mock()
        mock_adapter.initiate_payment.return_value = {
            'payment_url': 'https://wave.sn/pay/123',
            'transaction_id': 'tx-123',
        }
        self.mock_payment_factory.return_value = mock_adapter

        # Mock transaction crée
        mock_tx = Mock()
        mock_tx.id = 'tx-123'
        mock_tx.status = 'pending'
        self.mock_tx_repo.save.return_value = mock_tx

        result = self.uc.execute(
            buyer_id='buyer-123',
            parcel_id='parcel-123',
            provider='wave',
            otp_code='123456',
        )

        self.assertEqual(result['transaction_id'], 'tx-123')
        self.mock_tx_repo.save.assert_called_once()
        self.mock_notif.notify_payment_initiated.assert_called_once()

    def test_initiate_without_kyc(self):
        """Test sans KYC vérifié."""
        from core.exceptions.base import InvalidKYCStatusException

        mock_parcel = Mock()
        mock_parcel.is_certified = True
        self.mock_parcel_repo.get_by_id.return_value = mock_parcel

        mock_buyer = Mock()
        mock_buyer.is_kyc_verified = False
        self.mock_user_repo.get_by_id.return_value = mock_buyer

        with self.assertRaises(InvalidKYCStatusException):
            self.uc.execute(
                buyer_id='buyer-123',
                parcel_id='parcel-123',
                provider='wave',
            )


class TestConfirmPaymentUseCase(TestCase):
    """Tests du use case de confirmation."""

    def setUp(self):
        self.mock_tx_repo = Mock()
        self.mock_payment_factory = Mock()
        self.mock_notif = Mock()
        self.mock_audit = Mock()
        self.mock_celery = Mock()

        from apps.transactions.application.use_cases.payment import ConfirmPaymentUseCase
        self.uc = ConfirmPaymentUseCase(
            tx_repo=self.mock_tx_repo,
            payment_factory=self.mock_payment_factory,
            notification_service=self.mock_notif,
            audit_service=self.mock_audit,
            celery_app=self.mock_celery,
        )

    def test_confirm_payment_success(self):
        """Test de confirmation réussie."""
        mock_tx = Mock()
        mock_tx.id = 'tx-123'
        mock_tx.status = 'pending'
        mock_tx.parcel_id = 'parcel-123'
        self.mock_tx_repo.get_by_id.return_value = mock_tx

        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.verify_webhook.return_value = True
        mock_adapter.get_transaction_status.return_value = 'completed'
        self.mock_payment_factory.return_value = mock_adapter

        result = self.uc.execute(
            transaction_id='tx-123',
            provider='wave',
            webhook_data={'status': 'completed'},
        )

        self.assertTrue(result['success'])
        self.mock_tx_repo.save.assert_called_once()
        self.mock_celery.send_task.assert_called_once()  # Transfer ownership

    def test_confirm_invalid_webhook(self):
        """Test avec webhook invalide."""
        from core.exceptions.base import BusinessRuleViolationException

        mock_tx = Mock()
        self.mock_tx_repo.get_by_id.return_value = mock_tx

        mock_adapter = Mock()
        mock_adapter.verify_webhook.return_value = False
        self.mock_payment_factory.return_value = mock_adapter

        with self.assertRaises(BusinessRuleViolationException):
            self.uc.execute(
                transaction_id='tx-123',
                provider='wave',
                webhook_data={'status': 'completed'},
            )
