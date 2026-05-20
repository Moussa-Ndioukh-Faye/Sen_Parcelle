import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="transactions.check_pending")
def check_pending_transactions():
    """
    Vérifie les transactions en attente.
    Les transactions 'initiated' depuis plus de 30 min passent à 'failed'.
    """
    from apps.transactions.infrastructure.models import Transaction

    cutoff = timezone.now() - timedelta(minutes=30)
    stale = Transaction.objects.filter(
        status="initiated",
        created_at__lt=cutoff,
    )
    count = stale.count()
    if count:
        stale.update(status="failed", failure_reason="Délai d'attente dépassé")
        logger.info(f"{count} transactions expirées marquées 'failed'")
    else:
        logger.info("Aucune transaction en attente à nettoyer")
    return {"cleaned": count}
