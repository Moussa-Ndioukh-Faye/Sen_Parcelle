"""Tests des adapters de paiement (Orange Money, Wave) et des tâches transactions."""

import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.test import override_settings
from django.utils import timezone

from core.exceptions.base import ExternalServiceException

ORANGE_SETTINGS = override_settings(
    ORANGE_MONEY_CLIENT_ID="client",
    ORANGE_MONEY_CLIENT_SECRET="secret",
    ORANGE_MONEY_MERCHANT_KEY="merchant-key",
    ORANGE_MONEY_NOTIF_URL="https://api.test/notif",
    ORANGE_MONEY_RETURN_URL="https://app.test/ok",
    ORANGE_MONEY_CANCEL_URL="https://app.test/cancel",
)


def http_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def orange():
    from apps.transactions.infrastructure.adapters.orange_adapter import OrangeMoneyAdapter

    return OrangeMoneyAdapter()


class TestOrangeMoney:
    @ORANGE_SETTINGS
    @patch("apps.transactions.infrastructure.adapters.orange_adapter.requests.post")
    def test_initiate_payment(self, post):
        post.side_effect = [
            http_response({"access_token": "tok"}),
            http_response({"payment_url": "https://pay", "pay_token": "PT1"}),
        ]
        result = orange().initiate_payment(15000.0, "+221770000000", "REF1", "Achat parcelle")

        assert result == {"payment_url": "https://pay", "payment_ref": "PT1", "status": "pending"}
        payload = post.call_args_list[1].kwargs["json"]
        assert payload["amount"] == 15000
        assert payload["order_id"] == "REF1"
        assert post.call_args_list[1].kwargs["headers"]["Authorization"] == "Bearer tok"

    @ORANGE_SETTINGS
    @patch("apps.transactions.infrastructure.adapters.orange_adapter.requests.post")
    def test_initiate_payment_erreur_reseau(self, post):
        post.side_effect = requests.ConnectionError("timeout")
        with pytest.raises(ExternalServiceException):
            orange().initiate_payment(1000.0, "+221770000000", "REF1", "x")

    @ORANGE_SETTINGS
    @pytest.mark.parametrize(
        ("api_status", "expected"),
        [
            ("SUCCESS", "confirmed"),
            ("PENDING", "pending"),
            ("FAILED", "failed"),
            ("EXPIRED", "failed"),
            (None, "pending"),
        ],
    )
    def test_check_status(self, api_status, expected):
        with (
            patch(
                "apps.transactions.infrastructure.adapters.orange_adapter.requests.post",
                return_value=http_response({"access_token": "tok"}),
            ),
            patch(
                "apps.transactions.infrastructure.adapters.orange_adapter.requests.get",
                return_value=http_response({"status": api_status, "amount": "2500", "transaction_date": "2026"}),
            ),
        ):
            result = orange().check_status("PT1")
        assert result["status"] == expected
        assert result["amount"] == 2500.0

    @ORANGE_SETTINGS
    def test_check_status_erreur_reseau(self):
        with (
            patch(
                "apps.transactions.infrastructure.adapters.orange_adapter.requests.post",
                return_value=http_response({"access_token": "tok"}),
            ),
            patch(
                "apps.transactions.infrastructure.adapters.orange_adapter.requests.get",
                side_effect=requests.Timeout("lent"),
            ),
            pytest.raises(ExternalServiceException),
        ):
            orange().check_status("PT1")

    @ORANGE_SETTINGS
    def test_verify_webhook(self):
        payload = {"order_id": "REF1", "status": "SUCCESS"}
        body = json.dumps(payload, sort_keys=True)
        signature = hmac.new(b"merchant-key", body.encode(), hashlib.sha256).hexdigest()
        adapter = orange()
        assert adapter.verify_webhook(payload, signature) is True
        assert adapter.verify_webhook(payload, "mauvaise-signature") is False


def wave():
    from types import SimpleNamespace

    from apps.transactions.infrastructure.adapters.wave_adapter import WaveAdapter

    fake = SimpleNamespace(WAVE_API_KEY="wave-key", WAVE_SECRET_KEY="wave-secret", FRONTEND_URL="https://app.test")
    with patch("apps.transactions.infrastructure.adapters.wave_adapter.settings", fake):
        return WaveAdapter()


class TestWave:
    @pytest.mark.parametrize(
        ("api_status", "expected"),
        [("succeeded", "confirmed"), ("processing", "pending"), ("failed", "failed"), ("cancelled", "cancelled")],
    )
    def test_check_status(self, api_status, expected):
        data = {"payment_status": api_status, "amount": "5000", "client": {"mobile": "+221770000000"}}
        with patch(
            "apps.transactions.infrastructure.adapters.wave_adapter.requests.get",
            return_value=http_response(data),
        ):
            result = wave().check_status("cos-1")
        assert result["status"] == expected
        assert result["payer"] == "+221770000000"

    def test_check_status_erreur_reseau(self):
        with (
            patch(
                "apps.transactions.infrastructure.adapters.wave_adapter.requests.get",
                side_effect=requests.ConnectionError("down"),
            ),
            pytest.raises(ExternalServiceException),
        ):
            wave().check_status("cos-1")

    def test_verify_webhook(self):
        payload = {"id": "evt", "type": "checkout.session.completed"}
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(b"wave-secret", body.encode(), hashlib.sha256).hexdigest()
        adapter = wave()
        assert adapter.verify_webhook(payload, signature) is True
        assert adapter.verify_webhook(payload, "x") is False


@pytest.mark.django_db
class TestCheckPendingTransactions:
    def _transaction(self, django_user_model, created_at):
        from apps.parcels.infrastructure.models import Parcel
        from apps.transactions.infrastructure.models import Transaction

        n = Transaction.objects.count()
        seller = django_user_model.objects.create_user(
            email=f"vendeur{n}@test.sn", telephone=f"+22177000010{n}", password="x", nom="Vendeur"
        )
        buyer = django_user_model.objects.create_user(
            email=f"acheteur{n}@test.sn", telephone=f"+22177000020{n}", password="x", nom="Acheteur"
        )
        parcel = Parcel.objects.create(owner=seller, titre="Terrain", region="dakar", superficie=200, prix=1000)
        tx = Transaction.objects.create(parcel=parcel, buyer=buyer, seller=seller, amount_fcfa=1000, provider="wave")
        Transaction.objects.filter(pk=tx.pk).update(created_at=created_at)
        return tx

    def test_expire_les_transactions_anciennes(self, django_user_model):
        from apps.transactions.infrastructure.models import Transaction
        from apps.transactions.tasks import check_pending_transactions

        old = self._transaction(django_user_model, timezone.now() - timedelta(hours=1))
        recent = self._transaction(django_user_model, timezone.now())

        assert check_pending_transactions() == {"cleaned": 1}
        assert Transaction.objects.get(pk=old.pk).status == "failed"
        assert Transaction.objects.get(pk=recent.pk).status == "initiated"

    def test_rien_a_nettoyer(self):
        from apps.transactions.tasks import check_pending_transactions

        assert check_pending_transactions() == {"cleaned": 0}
