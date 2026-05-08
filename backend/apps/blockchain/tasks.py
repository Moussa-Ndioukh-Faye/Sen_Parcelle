"""
apps/blockchain/tasks.py + notifications/tasks.py
--------------------------------------------------
Tâches Celery asynchrones pour Sen_parcelle.
Principe : les opérations lentes ne bloquent jamais la réponse HTTP.
Flux : ViewSet → réponse 202 → Celery → résultat → notification.
"""

import logging
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


# ══════════════════════════════════════════════════════════════
# CELERY APP CONFIG
# infrastructure/celery/app.py
# ══════════════════════════════════════════════════════════════

"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("sen_parcelle")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Tâches planifiées (Celery Beat)
app.conf.beat_schedule = {
    "verifier-transactions-en-attente": {
        "task":     "transactions.check_pending",
        "schedule": 300.0,    # Toutes les 5 minutes
    },
    "cleanup-otp-expires": {
        "task":     "users.cleanup_expired_otp",
        "schedule": 600.0,    # Toutes les 10 minutes
    },
    "rapport-quotidien-admin": {
        "task":     "notifications.daily_report",
        "schedule": 86400.0,  # Une fois par jour
    },
}
"""


# ══════════════════════════════════════════════════════════════
# TÂCHES BLOCKCHAIN
# ══════════════════════════════════════════════════════════════

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,   # Retry après 60s
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
        from apps.parcels.infrastructure.models import DjangoParcelRepository
        from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
        from apps.blockchain.infrastructure.adapters.ipfs_adapter import IPFSAdapter
        from apps.notifications.services.notification_service import NotificationService
        from apps.audit.services import AuditService

        # ─── Charger la parcelle ───
        parcel_repo = DjangoParcelRepository()
        parcel      = parcel_repo.get_by_id(parcel_id)

        if parcel is None:
            logger.error(f"Parcelle introuvable : {parcel_id}")
            return {"success": False, "error": "Parcelle introuvable"}

        if parcel.blockchain_tx_hash:
            logger.warning(f"Parcelle déjà certifiée : {parcel_id}")
            return {"success": False, "error": "Déjà certifiée"}

        # ─── Upload sur IPFS ───
        ipfs   = IPFSAdapter()
        ipfs_hash = ipfs.pin_metadata({
            "parcel_id":      parcel_id,
            "document_hash":  parcel.document_hash,
            "titre":          parcel.titre,
            "region":         parcel.region,
            "surface":        parcel.surface,
            "owner_id":       parcel.owner_id,
        })
        logger.info(f"IPFS hash : {ipfs_hash}")

        # ─── Enregistrer sur Polygon ───
        polygon   = PolygonAdapter()
        tx_result = polygon.register_parcel(
            parcel_id=parcel_id,
            document_hash=parcel.document_hash,
            ipfs_hash=ipfs_hash,
            owner_address=polygon.get_owner_address(parcel.owner_id),
            localisation=f"{parcel.region} - {parcel.titre}",
            surface=int(parcel.surface),
            prix=int(parcel.price),
        )

        logger.info(f"TX Polygon : {tx_result['tx_hash']}")

        # ─── Mettre à jour la parcelle ───
        from apps.parcels.infrastructure.models import Parcel as ParcelORM
        from django.utils import timezone

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
                "parcel_id":   parcel_id,
                "titre":       parcel.titre,
                "tx_hash":     tx_result["tx_hash"],
            }
        )

        # ─── Audit ───
        AuditService().log(
            user_id=admin_id,
            action="parcel_certified",
            metadata={
                "parcel_id":  parcel_id,
                "tx_hash":    tx_result["tx_hash"],
                "ipfs_hash":  ipfs_hash,
            }
        )

        logger.info(f"✅ Parcelle certifiée : {parcel_id} → {tx_result['tx_hash']}")
        return {"success": True, "tx_hash": tx_result["tx_hash"], "ipfs_hash": ipfs_hash}

    except Exception as exc:
        logger.error(f"Erreur certification : parcel_id={parcel_id} error={exc}")
        # Retry automatique
        raise self.retry(exc=exc)


@shared_task(name="blockchain.transfer_ownership")
def transfer_ownership_on_blockchain(
    parcel_id: str, seller_id: str, buyer_id: str, transaction_id: str
):
    """
    Tâche Celery : transfère la propriété d'une parcelle sur Polygon.
    Déclenchée après confirmation du paiement.
    """
    logger.info(f"Transfert propriété blockchain : parcel={parcel_id}")

    try:
        from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
        from apps.parcels.infrastructure.models import Parcel as ParcelORM, DjangoParcelRepository
        from apps.transactions.infrastructure.models import Transaction as TxORM
        from apps.notifications.services.notification_service import NotificationService

        polygon = PolygonAdapter()
        parcel  = DjangoParcelRepository().get_by_id(parcel_id)

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
        notify.notify_user(buyer_id,  "ownership_transferred", {"parcel_id": parcel_id, "role": "buyer"})
        notify.notify_user(seller_id, "ownership_transferred", {"parcel_id": parcel_id, "role": "seller"})

        return {"success": True, "tx_hash": tx_result["tx_hash"]}

    except Exception as exc:
        logger.error(f"Erreur transfert ownership : {exc}")
        raise


# ══════════════════════════════════════════════════════════════
# TÂCHES NOTIFICATIONS
# ══════════════════════════════════════════════════════════════

@shared_task(name="notifications.send_sms")
def send_sms_async(to: str, message: str):
    """Envoi SMS asynchrone — ne bloque pas la requête HTTP."""
    from apps.users.infrastructure.adapters.sms_adapter import get_sms_adapter
    try:
        adapter = get_sms_adapter()
        adapter.send(to=to, message=message)
        logger.info(f"SMS envoyé (async) : to={to[:6]}***")
    except Exception as e:
        logger.error(f"Erreur SMS async : {e}")


@shared_task(name="notifications.send_push")
def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    """Notification push Firebase FCM."""
    import firebase_admin
    from firebase_admin import messaging, credentials
    from django.conf import settings
    from apps.users.infrastructure.models import User

    logger.info(f"Push notification : user={user_id} title={title}")
    
    try:
        # Initialisation unique de Firebase
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            firebase_admin.initialize_app(cred)

        # Récupérer le token FCM de l'utilisateur
        user = User.objects.get(id=user_id)
        fcm_token = getattr(user, "fcm_token", None)

        if not fcm_token:
            logger.warning(f"Pas de token FCM pour l'utilisateur {user_id}")
            return

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=fcm_token,
        )
        response = messaging.send(message)
        logger.info(f"Push envoyé avec succès : {response}")

    except Exception as e:
        logger.error(f"Erreur Push Firebase : {e}")


@shared_task(name="notifications.daily_report")
def send_daily_admin_report():
    """Rapport quotidien envoyé aux admins (statistiques)."""
    from apps.parcels.infrastructure.models import Parcel
    from apps.users.infrastructure.models import User
    from django.utils import timezone
    from datetime import timedelta
    from django.core.mail import send_mail
    from django.conf import settings

    yesterday = timezone.now() - timedelta(days=1)

    stats = {
        "new_users":            User.objects.filter(created_at__gte=yesterday).count(),
        "new_parcels":          Parcel.objects.filter(created_at__gte=yesterday).count(),
        "pending_parcels":      Parcel.objects.filter(status="pending").count(),
        "certified_yesterday":  Parcel.objects.filter(
                                    certified_at__gte=yesterday, status="certified"
                                ).count(),
        "pending_kyc":          User.objects.filter(kyc_status="pending").count(),
    }

    logger.info(f"Rapport quotidien : {stats}")
    
    report_message = f"""
    Rapport quotidien Sen_parcelle ({yesterday.date()})
    
    - Nouveaux utilisateurs : {stats['new_users']}
    - Nouvelles parcelles soumises : {stats['new_parcels']}
    - Parcelles certifiées blockchain : {stats['certified_yesterday']}
    - Parcelles en attente de validation : {stats['pending_parcels']}
    - Utilisateurs en attente de KYC : {stats['pending_kyc']}
    
    Consultez le dashboard : {settings.FRONTEND_URL}/admin
    """

    send_mail(
        subject=f"Sen_parcelle : Rapport quotidien {yesterday.date()}",
        message=report_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin[1] for admin in settings.ADMINS],
        fail_silently=False,
    )