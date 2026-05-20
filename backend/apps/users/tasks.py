import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="users.cleanup_expired_otp")
def cleanup_expired_otp():
    """
    Nettoie les codes OTP expirés ou déjà utilisés.
    Supprime les entrées de plus de 24h pour limiter la taille de la table.
    """
    from apps.users.infrastructure.models import OTPCode

    cutoff = timezone.now() - timezone.timedelta(hours=24)
    expired = OTPCode.objects.filter(expires_at__lt=cutoff)
    count = expired.count()
    expired.delete()
    logger.info(f"{count} codes OTP expirés nettoyés")
    return {"cleaned": count}
