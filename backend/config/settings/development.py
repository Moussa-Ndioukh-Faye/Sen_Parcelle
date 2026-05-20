from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Utiliser SQLite pour le développement local si GDAL n'est pas présent
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Cache local (pas de Redis nécessaire en dev)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

RATELIMIT_ENABLE = False
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
