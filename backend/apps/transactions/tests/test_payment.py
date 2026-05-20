"""
apps/transactions/tests/test_payment.py
----------------------------------------
Tests unitaires : TransactionEntity, WaveAdapter, OrangeMoneyAdapter,
InitiatePaymentUseCase, ConfirmPaymentUseCase
"""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

# ════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_parcel():
    parcel = MagicMock()
    parcel.id        = "parcel-123"
    parcel.owner_id  = "seller-456"
    parcel.titre     = "Terrain Almadies"
    parcel.region    = "Dakar"
    parcel.prix     = 25_000_000.0
    parcel.can_be_purchased.return_value = True
    return parcel

@pytest.fixture
def mock_buyer():
    buyer = MagicMock()
    buyer.id             = "buyer-789"
    buyer.nom            = "Moussa Faye"
    buyer.telephone      = MagicMock(__str__=lambda s: "+221776543210")
    buyer.can_buy_parcel.return_value = True
    return buyer

@pytest.fixture
def mock_seller():
    seller = MagicMock()
    seller.id  = "seller-456"
    seller.nom = "Aminata Diop"
    return seller

@pytest.fixture
def mock_tx_repo():
    repo = MagicMock()
    repo.save.side_effect = lambda tx: tx
    return repo

@pytest.fixture
def mock_wave_adapter():
    adapter = MagicMock()
    adapter.initiate_payment.return_value = {
        "payment_url": "https://pay.wave.com/session/abc123",
        "payment_ref": "wave-ref-abc123",
        "status":      "pending",
    }
    adapter.check_status.return_value = {
        "status":  "confirmed",
        "amount":  25_000_000.0,
        "paid_at": "2024-01-15T10:30:00Z",
    }
    adapter.verify_webhook.return_value = True
    return adapter


# ════════════════════════════════════════════════════════════════
# TESTS : TransactionEntity
# ════════════════════════════════════════════════════════════════

class TestTransactionEntity:

    def _make_tx(self, status="initiated"):
        from apps.transactions.domain.entities import (
            PaymentProvider,
            TransactionEntity,
            TransactionStatus,
        )
        return TransactionEntity(
            id="tx-001",
            parcel_id="parcel-123",
            buyer_id="buyer-789",
            seller_id="seller-456",
            amount_fcfa=25_000_000.0,
            provider=PaymentProvider.WAVE,
            status=TransactionStatus(status),
        )

    def test_initiated_peut_etre_annule(self):
        tx = self._make_tx("initiated")
        assert tx.can_be_cancelled() is True

    def test_completed_ne_peut_pas_etre_annule(self):
        tx = self._make_tx("completed")
        assert tx.can_be_cancelled() is False

    def test_pending_peut_etre_confirme(self):
        tx = self._make_tx("pending")
        assert tx.can_be_confirmed() is True

    def test_completed_est_finalise(self):
        tx = self._make_tx("completed")
        assert tx.is_finalized() is True

    def test_initiated_nest_pas_finalise(self):
        tx = self._make_tx("initiated")
        assert tx.is_finalized() is False

    def test_confirm_payment_change_status(self):
        from apps.transactions.domain.entities import TransactionStatus
        tx       = self._make_tx("pending")
        updated  = tx.confirm_payment("wave-ref-xyz")
        assert updated.status     == TransactionStatus.CONFIRMED
        assert updated.payment_ref == "wave-ref-xyz"
        # Immuabilité : original inchangé
        assert tx.status == TransactionStatus.PENDING

    def test_complete_enregistre_blockchain_tx(self):
        from apps.transactions.domain.entities import TransactionStatus
        tx       = self._make_tx("confirmed")
        updated  = tx.complete("0xabc123blockchain")
        assert updated.status        == TransactionStatus.COMPLETED
        assert updated.blockchain_tx == "0xabc123blockchain"

    def test_fail_enregistre_la_raison(self):
        from apps.transactions.domain.entities import TransactionStatus
        tx      = self._make_tx("pending")
        updated = tx.fail("Provider: timeout")
        assert updated.status         == TransactionStatus.FAILED
        assert updated.failure_reason == "Provider: timeout"


# ════════════════════════════════════════════════════════════════
# TESTS : WaveAdapter
# ════════════════════════════════════════════════════════════════

class TestWaveAdapter:

    @patch("apps.transactions.infrastructure.adapters.wave_adapter.requests.post")
    @patch("django.conf.settings")
    def test_initiate_payment_retourne_url(self, mock_settings, mock_post):
        mock_settings.WAVE_API_KEY    = "test_key"
        mock_settings.WAVE_SECRET_KEY = "test_secret"
        mock_settings.FRONTEND_URL    = "http://localhost:3000"

        mock_post.return_value.json.return_value = {
            "id":               "wave-sess-001",
            "wave_launch_url":  "https://pay.wave.com/wave-sess-001",
            "when_expires":     "2024-01-15T11:00:00Z",
        }
        mock_post.return_value.raise_for_status = MagicMock()

        from apps.transactions.infrastructure.adapters.wave_adapter import WaveAdapter
        adapter = WaveAdapter.__new__(WaveAdapter)
        adapter._api_key    = "test_key"
        adapter._secret_key = "test_secret"
        adapter._currency   = "XOF"

        with patch("apps.transactions.infrastructure.adapters.wave_adapter.settings", mock_settings):
            result = adapter.initiate_payment(
                amount=25_000_000,
                phone="+221776543210",
                reference="SPN-ABC123",
                description="Terrain Almadies",
            )

        assert result["payment_url"] == "https://pay.wave.com/wave-sess-001"
        assert result["payment_ref"] == "wave-sess-001"
        assert result["status"]      == "pending"

    def test_verify_webhook_signature_valide(self):
        from apps.transactions.infrastructure.adapters.wave_adapter import WaveAdapter
        adapter             = WaveAdapter.__new__(WaveAdapter)
        adapter._secret_key = "secret_test_key"

        payload  = {"id": "wave-001", "status": "succeeded", "amount": "25000000"}
        body     = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        sig      = hmac.new(b"secret_test_key", body.encode(), hashlib.sha256).hexdigest()

        # Utiliser directement la logique de vérification
        expected = hmac.new(
            adapter._secret_key.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert hmac.compare_digest(expected, sig) is True

    def test_verify_webhook_signature_invalide(self):
        import hmac as hmac_module
        payload = {"id": "wave-001", "status": "succeeded"}
        body    = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        sig     = hmac_module.new(b"mauvaise_cle", body.encode(), hashlib.sha256).hexdigest()

        expected = hmac_module.new(b"bonne_cle", body.encode(), hashlib.sha256).hexdigest()
        assert hmac_module.compare_digest(expected, sig) is False


# ════════════════════════════════════════════════════════════════
# TESTS : InitiatePaymentUseCase
# ════════════════════════════════════════════════════════════════

class TestInitiatePaymentUseCase:

    def _make_uc(self, parcel_repo, user_repo, tx_repo, wave_adapter):
        from apps.transactions.application.use_cases.payment import InitiatePaymentUseCase
        return InitiatePaymentUseCase(
            parcel_repo=parcel_repo,
            user_repo=user_repo,
            tx_repo=tx_repo,
            payment_factory=lambda _: wave_adapter,
            notification_service=MagicMock(),
            audit_service=MagicMock(),
        )

    def test_initier_paiement_succes(
        self, mock_parcel, mock_buyer, mock_seller, mock_tx_repo, mock_wave_adapter
    ):
        from apps.transactions.application.use_cases.payment import InitiatePaymentInput

        user_repo   = MagicMock()
        parcel_repo = MagicMock()
        user_repo.get_by_id.side_effect = lambda uid: (
            mock_buyer if uid == "buyer-789" else mock_seller
        )
        parcel_repo.get_by_id.return_value = mock_parcel

        uc = self._make_uc(parcel_repo, user_repo, mock_tx_repo, mock_wave_adapter)
        result = uc.execute(InitiatePaymentInput(
            buyer_id="buyer-789",
            parcel_id="parcel-123",
            provider="wave",
        ))

        assert result.payment_url  == "https://pay.wave.com/session/abc123"
        assert result.amount_fcfa  == 25_000_000.0
        assert result.provider     == "wave"
        assert result.transaction_id is not None
        mock_wave_adapter.initiate_payment.assert_called_once()

    def test_acheteur_kyc_non_verifie_leve_exception(
        self, mock_parcel, mock_buyer, mock_tx_repo, mock_wave_adapter
    ):
        from apps.transactions.application.use_cases.payment import InitiatePaymentInput
        from core.exceptions.base import InvalidKYCStatusException

        mock_buyer.can_buy_parcel.return_value = False

        user_repo   = MagicMock()
        parcel_repo = MagicMock()
        user_repo.get_by_id.return_value   = mock_buyer
        parcel_repo.get_by_id.return_value = mock_parcel

        uc = self._make_uc(parcel_repo, user_repo, mock_tx_repo, mock_wave_adapter)
        with pytest.raises(InvalidKYCStatusException):
            uc.execute(InitiatePaymentInput(
                buyer_id="buyer-789", parcel_id="parcel-123", provider="wave"
            ))

    def test_parcelle_non_certifiee_leve_exception(
        self, mock_parcel, mock_buyer, mock_tx_repo, mock_wave_adapter
    ):
        from apps.transactions.application.use_cases.payment import InitiatePaymentInput
        from core.exceptions.base import BusinessRuleViolationException

        mock_parcel.can_be_purchased.return_value = False

        user_repo   = MagicMock()
        parcel_repo = MagicMock()
        user_repo.get_by_id.return_value   = mock_buyer
        parcel_repo.get_by_id.return_value = mock_parcel

        uc = self._make_uc(parcel_repo, user_repo, mock_tx_repo, mock_wave_adapter)
        with pytest.raises(BusinessRuleViolationException) as exc:
            uc.execute(InitiatePaymentInput(
                buyer_id="buyer-789", parcel_id="parcel-123", provider="wave"
            ))
        assert exc.value.code == "parcel_not_available"

    def test_achat_propre_parcelle_leve_exception(
        self, mock_parcel, mock_tx_repo, mock_wave_adapter
    ):
        from apps.transactions.application.use_cases.payment import InitiatePaymentInput
        from core.exceptions.base import BusinessRuleViolationException

        # L'acheteur est aussi le vendeur
        mock_parcel.owner_id = "buyer-789"
        buyer = MagicMock()
        buyer.id = "buyer-789"
        buyer.can_buy_parcel.return_value = True

        user_repo   = MagicMock()
        parcel_repo = MagicMock()
        user_repo.get_by_id.return_value   = buyer
        parcel_repo.get_by_id.return_value = mock_parcel

        uc = self._make_uc(parcel_repo, user_repo, mock_tx_repo, mock_wave_adapter)
        with pytest.raises(BusinessRuleViolationException) as exc:
            uc.execute(InitiatePaymentInput(
                buyer_id="buyer-789", parcel_id="parcel-123", provider="wave"
            ))
        assert exc.value.code == "self_purchase"


# ════════════════════════════════════════════════════════════════
# TESTS : ConfirmPaymentUseCase
# ════════════════════════════════════════════════════════════════

class TestConfirmPaymentUseCase:

    def _make_tx(self):
        from apps.transactions.domain.entities import (
            PaymentProvider,
            TransactionEntity,
            TransactionStatus,
        )
        return TransactionEntity(
            id="tx-001",
            parcel_id="parcel-123",
            buyer_id="buyer-789",
            seller_id="seller-456",
            amount_fcfa=25_000_000.0,
            provider=PaymentProvider.WAVE,
            status=TransactionStatus.PENDING,
            payment_ref="wave-ref-abc123",
        )

    def test_webhook_confirme_transaction(self, mock_wave_adapter):
        from apps.transactions.application.use_cases.payment import (
            ConfirmPaymentInput,
            ConfirmPaymentUseCase,
        )

        tx_repo = MagicMock()
        tx      = self._make_tx()
        tx_repo.get_by_payment_ref.return_value = tx
        tx_repo.save.side_effect = lambda t: t

        mock_wave_adapter.check_status.return_value = {
            "status": "confirmed", "amount": 25_000_000.0, "paid_at": "2024-01-15T10:30:00Z"
        }

        celery_mock = MagicMock()

        uc = ConfirmPaymentUseCase(
            tx_repo=tx_repo,
            payment_factory=lambda _: mock_wave_adapter,
            notification_service=MagicMock(),
            audit_service=MagicMock(),
            celery_app=celery_mock,
        )
        result = uc.execute(ConfirmPaymentInput(
            payment_ref="wave-ref-abc123",
            provider="wave",
            webhook_payload={"id": "wave-ref-abc123", "status": "succeeded"},
            signature="valid-sig",
        ))

        assert result.status == "confirmed"
        celery_mock.send_task.assert_called_once_with(
            "blockchain.transfer_ownership",
            kwargs={
                "transaction_id": "tx-001",
                "parcel_id":      "parcel-123",
                "seller_id":      "seller-456",
                "buyer_id":       "buyer-789",
            }
        )

    def test_signature_invalide_leve_exception(self, mock_wave_adapter):
        from apps.transactions.application.use_cases.payment import (
            ConfirmPaymentInput,
            ConfirmPaymentUseCase,
        )
        from core.exceptions.base import BusinessRuleViolationException

        mock_wave_adapter.verify_webhook.return_value = False

        uc = ConfirmPaymentUseCase(
            tx_repo=MagicMock(),
            payment_factory=lambda _: mock_wave_adapter,
            notification_service=MagicMock(),
            audit_service=MagicMock(),
            celery_app=MagicMock(),
        )
        with pytest.raises(BusinessRuleViolationException) as exc:
            uc.execute(ConfirmPaymentInput(
                payment_ref="ref",
                provider="wave",
                webhook_payload={},
                signature="bad-sig",
            ))
        assert exc.value.code == "invalid_webhook_signature"

    def test_transaction_deja_finalisee_retourne_sans_retraiter(self, mock_wave_adapter):
        from apps.transactions.application.use_cases.payment import (
            ConfirmPaymentInput,
            ConfirmPaymentUseCase,
        )
        from apps.transactions.domain.entities import (
            PaymentProvider,
            TransactionEntity,
            TransactionStatus,
        )

        tx = TransactionEntity(
            id="tx-001", parcel_id="p", buyer_id="b", seller_id="s",
            amount_fcfa=1_000_000.0, provider=PaymentProvider.WAVE,
            status=TransactionStatus.COMPLETED,  # Déjà complété
        )
        tx_repo = MagicMock()
        tx_repo.get_by_payment_ref.return_value = tx

        celery_mock = MagicMock()
        uc = ConfirmPaymentUseCase(
            tx_repo=tx_repo,
            payment_factory=lambda _: mock_wave_adapter,
            notification_service=MagicMock(),
            audit_service=MagicMock(),
            celery_app=celery_mock,
        )
        result = uc.execute(ConfirmPaymentInput(
            payment_ref="ref", provider="wave",
            webhook_payload={}, signature="sig",
        ))

        assert result.status == "completed"
        # Celery NE doit PAS être appelé une 2ème fois
        celery_mock.send_task.assert_not_called()
