"""
apps/blockchain/tasks.py
Tâches Celery asynchrones pour la blockchain Sen_parcelle.
"""

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry après 60s
    name="blockchain.certify_parcel",
)
def certify_parcel_on_blockchain(self, parcel_id: str, admin_id: str):
    """
    Tâche Celery : certifie une parcelle sur Polygon.
    Déclenchée après validation admin.

    Retry automatique en cas d'échec (max 3 fois).
    """
    logger.info(f"Démarrage certification blockchain : parcel_id={parcel_id}")

    try:
        from apps.audit.services import AuditService
        from apps.blockchain.infrastructure.adapters.ipfs_adapter import IPFSAdapter
        from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
        from apps.notifications.services.notification_service import NotificationService
        from apps.parcels.infrastructure.models import DjangoParcelRepository

        # ─── Charger la parcelle ───
        parcel_repo = DjangoParcelRepository()
        parcel = parcel_repo.get_by_id(parcel_id)

        if parcel is None:
            logger.error(f"Parcelle introuvable : {parcel_id}")
            return {"success": False, "error": "Parcelle introuvable"}

        if parcel.blockchain_tx_hash:
            logger.warning(f"Parcelle déjà certifiée : {parcel_id}")
            return {"success": False, "error": "Déjà certifiée"}

        # ─── Upload sur IPFS ───
        ipfs = IPFSAdapter()
        ipfs_hash = ipfs.pin_metadata(
            {
                "parcel_id": parcel_id,
                "document_hash": parcel.document_hash,
                "titre": parcel.titre,
                "region": parcel.region,
                "superficie": parcel.superficie,
                "prix": parcel.prix,
                "localisation": parcel.localisation,
                "type_terrain": parcel.type_terrain.value,
                "owner_id": parcel.owner_id,
            }
        )
        logger.info(f"IPFS hash : {ipfs_hash}")

        # ─── Enregistrer sur Polygon ───
        polygon = PolygonAdapter()
        tx_result = polygon.register_parcel(
            parcel_id=parcel_id,
            document_hash=parcel.document_hash,
            ipfs_hash=ipfs_hash,
            owner_address=polygon.get_owner_address(parcel.owner_id),
            localisation=parcel.localisation,
            superficie=int(parcel.superficie),
            prix=int(parcel.prix),
        )

        logger.info(f"TX Polygon : {tx_result['tx_hash']}")

        # ─── Mettre à jour la parcelle ───
        from django.utils import timezone

        from apps.parcels.infrastructure.models import Parcel as ParcelORM

        ParcelORM.objects.filter(id=parcel_id).update(
            status="certified",
            blockchain_tx_hash=tx_result["tx_hash"],
            ipfs_hash=ipfs_hash,
            certified_at=timezone.now(),
        )

        # ─── Notifier le vendeur ───
        NotificationService().notify_user(
            user_id=parcel.owner_id,
            event="parcel_certified",
            data={
                "parcel_id": parcel_id,
                "titre": parcel.titre,
                "tx_hash": tx_result["tx_hash"],
            },
        )

        # ─── Audit ───
        AuditService().log(
            user_id=admin_id,
            action="parcel_certified",
            metadata={
                "parcel_id": parcel_id,
                "tx_hash": tx_result["tx_hash"],
                "ipfs_hash": ipfs_hash,
            },
        )

        logger.info(f"✅ Parcelle certifiée : {parcel_id} → {tx_result['tx_hash']}")
        return {"success": True, "tx_hash": tx_result["tx_hash"], "ipfs_hash": ipfs_hash}

    except Exception as exc:
        logger.error(f"Erreur certification : parcel_id={parcel_id} error={exc}")
        # Retry automatique
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="blockchain.transfer_ownership")
def transfer_ownership_on_blockchain(self, parcel_id: str, seller_id: str, buyer_id: str, transaction_id: str):
    """
    Tâche Celery : transfère la propriété d'une parcelle sur Polygon.
    Déclenchée après confirmation du paiement.
    """
    logger.info(f"Transfert propriété blockchain : parcel={parcel_id}")

    try:
        from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
        from apps.notifications.services.notification_service import NotificationService
        from apps.parcels.infrastructure.models import Parcel as ParcelORM
        from apps.transactions.infrastructure.models import Transaction as TxORM

        polygon = PolygonAdapter()

        tx_result = polygon.transfer_ownership(
            parcel_id=parcel_id,
            new_owner=polygon.get_owner_address(buyer_id),
            tx_ref=transaction_id,
        )

        # ─── Mettre à jour propriétaire ───
        ParcelORM.objects.filter(id=parcel_id).update(
            owner_id=buyer_id,
            status="sold",
        )

        TxORM.objects.filter(id=transaction_id).update(
            status="completed",
            blockchain_tx_hash=tx_result["tx_hash"],
        )

        # ─── Notifier acheteur et vendeur ───
        notify = NotificationService()
        notify.notify_user(buyer_id, "ownership_transferred", {"parcel_id": parcel_id, "role": "buyer"})
        notify.notify_user(seller_id, "ownership_transferred", {"parcel_id": parcel_id, "role": "seller"})

        return {"success": True, "tx_hash": tx_result["tx_hash"]}

    except Exception as exc:
        logger.error(f"Erreur transfert ownership : {exc}")
        raise self.retry(exc=exc)


# Note : les tâches notifications (send_sms, send_push, daily_report)
# ont été déplacées vers apps/notifications/tasks.py
