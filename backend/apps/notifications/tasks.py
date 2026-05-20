"""
apps/notifications/tasks.py
Tâches Celery asynchrones pour les notifications.
"""

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


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
def send_push_notification(user_id: str, title: str, body: str, data: dict | None = None):
    """Notification push Firebase FCM."""
    import firebase_admin
    from django.conf import settings
    from firebase_admin import credentials, messaging

    from apps.users.infrastructure.models import User

    logger.info(f"Push notification : user={user_id} title={title}")

    try:
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            firebase_admin.initialize_app(cred)

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
    from datetime import timedelta

    from django.conf import settings
    from django.core.mail import send_mail
    from django.utils import timezone

    from apps.parcels.infrastructure.models import Parcel
    from apps.users.infrastructure.models import User

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
