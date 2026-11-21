# ══════════════════════════════════════════════════════════════
# ADAPTER SMS — Twilio (production) + Console (dev)
# apps/users/infrastructure/adapters/sms_adapter.py
# ══════════════════════════════════════════════════════════════

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ISMSAdapter(ABC):
    @abstractmethod
    def send(self, to: str, message: str) -> bool: ...


class TwilioSMSAdapter(ISMSAdapter):
    """
    Adapter SMS production via Twilio.
    Supporte les numéros sénégalais (+221).
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        from twilio.rest import Client

        self._client = Client(account_sid, auth_token)
        self._from_number = from_number

    def send(self, to: str, message: str) -> bool:
        try:
            msg = self._client.messages.create(
                body=message,
                from_=self._from_number,
                to=to,
            )
            logger.info(f"SMS envoyé : to={to} sid={msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Erreur SMS Twilio : to={to} error={e}")
            from core.exceptions.base import ExternalServiceException

            raise ExternalServiceException("Twilio SMS", str(e))


class ConsoleSMSAdapter(ISMSAdapter):
    """
    Adapter SMS développement : affiche dans les logs.
    Activé automatiquement si DEBUG=True.
    """

    def send(self, to: str, message: str) -> bool:
        logger.info(f"\n{'=' * 50}\n📱 SMS → {to}\n{message}\n{'=' * 50}")
        return True


class OrangeSMSSenegalAdapter(ISMSAdapter):
    """
    Adapter Orange Money SMS Sénégal.
    API locale plus économique pour les numéros +221.
    """

    def __init__(self, api_key: str, sender_id: str):
        self._api_key = api_key
        self._sender_id = sender_id

    def send(self, to: str, message: str) -> bool:
        import requests

        try:
            response = requests.post(
                "https://api.orange.sn/smsmessaging/v1/outbound/send",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "outboundSMSMessageRequest": {
                        "address": [f"tel:{to}"],
                        "senderAddress": f"tel:{self._sender_id}",
                        "outboundSMSTextMessage": {"message": message},
                    }
                },
                timeout=10,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erreur Orange SMS : {e}")
            from core.exceptions.base import ExternalServiceException

            raise ExternalServiceException("Orange SMS", str(e))


# ══════════════════════════════════════════════════════════════
# FACTORY — Sélection automatique de l'adapter
# ══════════════════════════════════════════════════════════════


def get_sms_adapter() -> ISMSAdapter:
    """
    Retourne l'adapter SMS selon la configuration.
    Pattern Factory — découple la config du code.
    """
    from django.conf import settings

    if getattr(settings, "DEBUG", False):
        return ConsoleSMSAdapter()

    provider = getattr(settings, "SMS_PROVIDER", "twilio")

    if provider == "twilio":
        twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        if not twilio_sid:
            logger.warning("TWILIO_ACCOUNT_SID non configuré — fallback ConsoleSMSAdapter")
            return ConsoleSMSAdapter()
        return TwilioSMSAdapter(
            account_sid=twilio_sid,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_number=settings.TWILIO_FROM_NUMBER,
        )
    elif provider == "orange":
        return OrangeSMSSenegalAdapter(
            api_key=settings.ORANGE_SMS_API_KEY,
            sender_id=settings.ORANGE_SMS_SENDER_ID,
        )

    raise ValueError(f"SMS provider inconnu : {provider}")
