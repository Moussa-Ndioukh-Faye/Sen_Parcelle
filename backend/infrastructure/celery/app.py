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
        "schedule": 300.0,
    },
    "cleanup-otp-expires": {
        "task":     "users.cleanup_expired_otp",
        "schedule": 600.0,
    },
    "rapport-quotidien-admin": {
        "task":     "notifications.daily_report",
        "schedule": 86400.0,
    },
}
