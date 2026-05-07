# ════════════════════════════════════════════════════════════════
# ADAPTER ORANGE MONEY SÉNÉGAL
# apps/transactions/infrastructure/adapters/orange_adapter.py
# ════════════════════════════════════════════════════════════════

import hashlib
import hmac
import logging
import requests
from django.conf import settings
from core.exceptions.base import ExternalServiceException
from apps.transactions.domain.entities import IPaymentAdapter

logger = logging.getLogger(__name__)


class OrangeMoneyAdapter(IPaymentAdapter):
    """
    Adapter Orange Money Sénégal.
    API Orange Money : https://developer.orange.com/apis/om-webpay-sn

    Flux :
    1. POST /token → obtenir access_token OAuth2
    2. POST /webpayment → initier le paiement
    3. Recevoir callback URL
    4. GET /paymentstatus → vérifier confirmation
    """

    TOKEN_URL   = "https://api.orange.com/oauth/v3/token"
    BASE_URL    = "https://api.orange.com/orange-money-webpay/sn/v1"
    TIMEOUT     = 30

    def __init__(self):
        self._client_id     = settings.ORANGE_MONEY_CLIENT_ID
        self._client_secret = settings.ORANGE_MONEY_CLIENT_SECRET
        self._merchant_key  = settings.ORANGE_MONEY_MERCHANT_KEY
        self._notif_url     = settings.ORANGE_MONEY_NOTIF_URL
        self._return_url    = settings.ORANGE_MONEY_RETURN_URL
        self._cancel_url    = settings.ORANGE_MONEY_CANCEL_URL

    def _get_token(self) -> str:
        """OAuth2 : récupère un access token."""
        import base64
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        response = requests.post(
            self.TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def initiate_payment(
        self,
        amount:      float,
        phone:       str,
        reference:   str,
        description: str,
    ) -> dict:
        """Initie un paiement Orange Money."""
        try:
            token = self._get_token()
            phone_clean = phone.replace("+221", "").replace(" ", "")

            payload = {
                "merchant_key": self._merchant_key,
                "currency":     "OUV",    # Code devise Orange Money SN
                "order_id":     reference,
                "amount":       int(amount),
                "return_url":   self._return_url,
                "cancel_url":   self._cancel_url,
                "notif_url":    self._notif_url,
                "lang":         "fr",
                "reference":    description,
            }

            response = requests.post(
                f"{self.BASE_URL}/webpayment",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                },
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Orange Money initié : ref={reference} id={data.get('pay_token')}")
            return {
                "payment_url": data["payment_url"],
                "payment_ref": data["pay_token"],
                "status":      "pending",
            }
        except requests.RequestException as e:
            logger.error(f"Erreur Orange Money initiate : {e}")
            raise ExternalServiceException("Orange Money", str(e))

    def check_status(self, payment_ref: str) -> dict:
        """Vérifie le statut d'un paiement Orange Money."""
        try:
            token = self._get_token()
            response = requests.get(
                f"{self.BASE_URL}/paymentstatus",
                params={"order_id": payment_ref},
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            status_map = {
                "SUCCESS":  "confirmed",
                "PENDING":  "pending",
                "FAILED":   "failed",
                "EXPIRED":  "failed",
            }
            return {
                "status": status_map.get(data.get("status"), "pending"),
                "amount": float(data.get("amount", 0)),
                "paid_at": data.get("transaction_date"),
            }
        except requests.RequestException as e:
            raise ExternalServiceException("Orange Money", str(e))

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Vérifie la signature d'un webhook Orange Money."""
        import json
        data     = json.dumps(payload, sort_keys=True)
        expected = hmac.new(
            self._merchant_key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)