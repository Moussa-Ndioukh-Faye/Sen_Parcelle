# ════════════════════════════════════════════════════════════════
# ADAPTER WAVE SÉNÉGAL
# apps/transactions/infrastructure/adapters/wave_adapter.py
# ════════════════════════════════════════════════════════════════

import hashlib
import hmac
import logging

import requests
from django.conf import settings

from apps.transactions.domain.entities import IPaymentAdapter
from core.exceptions.base import ExternalServiceException

logger = logging.getLogger(__name__)


class WaveAdapter(IPaymentAdapter):
    """
    Adapter Wave Sénégal.
    Documentation : https://developer.wave.com/docs

    Flux :
    1. POST /v1/checkout/sessions → obtenir payment_url
    2. Rediriger l'utilisateur vers payment_url
    3. Recevoir webhook confirmation
    4. Vérifier signature HMAC
    """

    BASE_URL  = "https://api.wave.com/v1"
    TIMEOUT   = 30

    def __init__(self):
        self._api_key    = settings.WAVE_API_KEY
        self._secret_key = settings.WAVE_SECRET_KEY
        self._currency   = "XOF"   # Franc CFA

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type":  "application/json",
            "X-Currency":    self._currency,
        }

    def initiate_payment(
        self,
        amount:      float,
        phone:       str,
        reference:   str,
        description: str,
    ) -> dict:
        """
        Crée une session de paiement Wave.
        Retourne l'URL de paiement.
        """
        payload = {
            "currency":          self._currency,
            "amount":            str(int(amount)),
            "client_reference":  reference,
            "success_url":       f"{settings.FRONTEND_URL}/paiement/success?ref={reference}",
            "error_url":         f"{settings.FRONTEND_URL}/paiement/error?ref={reference}",
            "restrict_payer_mobile": phone.replace("+221", "").replace(" ", ""),
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/checkout/sessions",
                json=payload,
                headers=self._headers(),
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Wave session créée : ref={reference} id={data.get('id')}")
            return {
                "payment_url": data["wave_launch_url"],
                "payment_ref": data["id"],
                "status":      "pending",
                "expires_at":  data.get("when_expires"),
            }

        except requests.RequestException as e:
            logger.error(f"Erreur Wave initiate : {e}")
            raise ExternalServiceException("Wave", str(e))

    def check_status(self, payment_ref: str) -> dict:
        """Vérifie le statut d'une session Wave."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/checkout/sessions/{payment_ref}",
                headers=self._headers(),
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            status_map = {
                "processing": "pending",
                "succeeded":  "confirmed",
                "failed":     "failed",
                "cancelled":  "cancelled",
            }

            return {
                "status":   status_map.get(data.get("payment_status"), "pending"),
                "amount":   float(data.get("amount", 0)),
                "paid_at":  data.get("when_completed"),
                "payer":    data.get("client", {}).get("mobile", ""),
            }
        except requests.RequestException as e:
            raise ExternalServiceException("Wave", str(e))

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """
        Vérifie la signature HMAC-SHA256 du webhook Wave.
        """
        import json
        body     = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        expected = hmac.new(
            self._secret_key.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
