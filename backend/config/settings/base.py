# ══════════════════════════════════════════════════════════════
# config/settings/base.py — Configuration commune
# ══════════════════════════════════════════════════════════════

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set via environment variable")
DEBUG      = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# ─── Applications ───
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",              # PostGIS
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_ratelimit",
    "celery",
    "django_celery_beat",
    "drf_spectacular",
    "health_check",
    "health_check.cache",
    "health_check.storage",
    "storages",                        # django-storages (S3)
]

LOCAL_APPS = [
    "core",
    "apps.users",
    "apps.parcels",
    "apps.transactions",
    "apps.blockchain",
    "apps.notifications",
    "apps.audit",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditMiddleware",        # Log toutes les requêtes
    "core.utils.crypto.SecurityHeadersMiddleware",   # Headers sécurité HTTP
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ——— Base de données PostGIS ———
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ─── Cache Redis ───
CACHES = {
    "default": {
        "BACKEND":  "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        "OPTIONS":  {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# ─── Celery (tâches async) ───
CELERY_BROKER_URL    = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TIMEZONE        = "Africa/Dakar"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ─── JWT ───
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=15),   # Court pour la sécurité
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─── DRF ───
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.jwt_auth.JWTServiceAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS":  "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.base.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ─── drf-spectacular (Swagger/OpenAPI) ───
SPECTACULAR_SETTINGS = {
    "TITLE": "Sen_Parcelle API",
    "DESCRIPTION": "Plateforme foncière sécurisée — Sénégal",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {
        "email": "contact@sen-parcelle.sn",
    },
    "LICENSE": {
        "name": "MIT",
    },
    "SCHEMA_PATH_PREFIX": "/api/",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}

# ─── CORS (Flutter + Angular) ───
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")
CORS_ALLOW_CREDENTIALS = True

# ─── AWS S3 ───
AWS_ACCESS_KEY_ID       = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY   = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_BUCKET", "sen-parcelle-media")
AWS_S3_REGION_NAME      = os.environ.get("AWS_REGION", "eu-west-1")
AWS_S3_CUSTOM_DOMAIN    = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"ServerSideEncryption": "AES256"}
AWS_DEFAULT_ACL         = "private"
DEFAULT_FILE_STORAGE    = "storages.backends.s3boto3.S3Boto3Storage"

# ─── Sécurité HTTP ───
SECURE_BROWSER_XSS_FILTER     = True
X_FRAME_OPTIONS                = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF   = True
SECURE_SSL_REDIRECT            = bool(int(os.environ.get("SECURE_SSL_REDIRECT", "1")))
SESSION_COOKIE_SECURE          = bool(int(os.environ.get("SESSION_COOKIE_SECURE", "1")))
CSRF_COOKIE_SECURE             = bool(int(os.environ.get("CSRF_COOKIE_SECURE", "1")))
SESSION_COOKIE_HTTPONLY        = True
CSRF_COOKIE_HTTPONLY           = True
SESSION_COOKIE_SAMESITE        = "Lax"
CSRF_COOKIE_SAMESITE           = "Lax"
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
DATA_UPLOAD_MAX_MEMORY_SIZE    = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE    = 20 * 1024 * 1024

# ─── Internationalisation ───
LANGUAGE_CODE = "fr-SN"
TIME_ZONE     = "Africa/Dakar"
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

# ─── Blockchain Polygon ───
POLYGON_RPC_URL         = os.environ.get("POLYGON_RPC_URL", "http://localhost:8545")
POLYGON_PRIVATE_KEY     = os.environ.get("POLYGON_PRIVATE_KEY", "")
POLYGON_CONTRACT_ADDRESS = os.environ.get("POLYGON_CONTRACT_ADDRESS", "")
POLYGON_CHAIN_ID        = int(os.environ.get("POLYGON_CHAIN_ID", "80001"))

# ─── Sentry (Observabilité / Error Tracking) ───
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACE_RATE", "0.1")),
        send_default_pii=False,
        environment=os.environ.get("DJANGO_ENV", "production"),
    )

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

