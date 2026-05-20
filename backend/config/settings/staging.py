from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,staging.sen-parcelle.sn").split(",")  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "sen_parcelle_staging"),  # noqa: F405
        "USER": os.environ.get("DB_USER", "sen_parcelle"),  # noqa: F405
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),  # noqa: F405
        "HOST": os.environ.get("DB_HOST", "localhost"),  # noqa: F405
        "PORT": os.environ.get("DB_PORT", "5432"),  # noqa: F405
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),  # noqa: F405
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# Use local file storage for staging (no real S3)
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Staging-specific Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.5,
        environment="staging",
    )

# Logging to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
