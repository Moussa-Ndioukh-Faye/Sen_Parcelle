"""
config/settings/production.py
─────────────────────────────────────────────────
Settings for production environment.
─────────────────────────────────────────────────
"""

from .base import *

# ═════════════════════════════════════════════════════════════
# SECURITY
# ═════════════════════════════════════════════════════════════

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY est obligatoire en production. "
        "Définissez la variable d'environnement SECRET_KEY."
    )

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# ═════════════════════════════════════════════════════════════
# DATABASE
# ═════════════════════════════════════════════════════════════

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME":     os.environ.get("DB_NAME", "sen_parcelle_db"),
        "USER":     os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST":     os.environ.get("DB_HOST", "localhost"),
        "PORT":     os.environ.get("DB_PORT", "5432"),
    }
}

# ═════════════════════════════════════════════════════════════
# REDIS
# ═════════════════════════════════════════════════════════════

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# ═════════════════════════════════════════════════════════════
# CORS
# ═════════════════════════════════════════════════════════════

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

# ═════════════════════════════════════════════════════════════
# AWS S3
# ═════════════════════════════════════════════════════════════

AWS_ACCESS_KEY_ID     = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET          = os.environ.get("AWS_BUCKET")
AWS_REGION           = os.environ.get("AWS_REGION", "eu-west-1")

# ═════════════════════════════════════════════════════════════
# BLOCKCHAIN
# ═════════════════════════════════════════════════════════════

POLYGON_RPC_URL        = os.environ.get("POLYGON_RPC_URL")
POLYGON_PRIVATE_KEY     = os.environ.get("POLYGON_PRIVATE_KEY")
POLYGON_CONTRACT_ADDRESS = os.environ.get("POLYGON_CONTRACT_ADDRESS")
POLYGONSCAN_API_KEY    = os.environ.get("POLYGONSCAN_API_KEY")

# ═════════════════════════════════════════════════════════════
# IPFS (Pinata)
# ═════════════════════════════════════════════════════════════

PINATA_JWT    = os.environ.get("PINATA_JWT")
IPFS_GATEWAY = os.environ.get("IPFS_GATEWAY", "https://gateway.pinata.cloud/ipfs")

# ═════════════════════════════════════════════════════════════
# PAYMENTS
# ═════════════════════════════════════════════════════════════

WAVE_API_KEY        = os.environ.get("WAVE_API_KEY")
WAVE_SECRET_KEY    = os.environ.get("WAVE_SECRET_KEY")

ORANGE_MONEY_CLIENT_ID     = os.environ.get("ORANGE_MONEY_CLIENT_ID")
ORANGE_MONEY_CLIENT_SECRET = os.environ.get("ORANGE_MONEY_CLIENT_SECRET")
ORANGE_MONEY_MERCHANT_KEY  = os.environ.get("ORANGE_MONEY_MERCHANT_KEY")

# ═════════════════════════════════════════════════════════════
# SMS
# ═════════════════════════════════════════════════════════════

SMS_PROVIDER     = os.environ.get("SMS_PROVIDER", "twilio")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
