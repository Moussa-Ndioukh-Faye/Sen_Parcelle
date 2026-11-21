import os

from .base import *  # noqa: F403

DEBUG = bool(int(os.environ.get("DEBUG", "1")))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", "/data/db.sqlite3"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_BROKER_URL = "memory://"

INSTALLED_APPS = [
    app
    for app in INSTALLED_APPS  # noqa: F405
    if app not in ("django.contrib.gis", "django_celery_beat", "django_redis")
]

MIDDLEWARE = [m for m in MIDDLEWARE if "SecurityHeadersMiddleware" not in m]  # noqa: F405

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:80,http://localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:80").split(",")

if not os.environ.get("AWS_ACCESS_KEY_ID"):
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

if not os.environ.get("SENTRY_DSN"):
    SENTRY_DSN = None

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
