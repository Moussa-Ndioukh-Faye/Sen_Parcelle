import sys
from unittest.mock import MagicMock

# ─── Mock GDAL/GIS for environments without GIS (CI / local Windows) ───
try:
    import django.contrib.gis.gdal  # noqa: F401 — probe GDAL availability
except Exception:
    from django.db import models

    class MockPointField(models.JSONField):
        def __init__(self, *args, **kwargs):
            kwargs.pop("geography", None)
            kwargs.pop("srid", None)
            super().__init__(*args, **kwargs)

    mock_gis = MagicMock()
    mock_gis.db.models.fields.PointField = MockPointField
    mock_gis.db.models.PointField = MockPointField
    mock_gis.geos.Point = MagicMock()
    mock_gis.measure.Distance = MagicMock()
    mock_gis.db.models.functions.GeoFunc = MagicMock()

    sys.modules["django.contrib.gis"] = mock_gis
    sys.modules["django.contrib.gis.db"] = mock_gis.db
    sys.modules["django.contrib.gis.db.models"] = mock_gis.db.models
    sys.modules["django.contrib.gis.db.models.fields"] = mock_gis.db.models.fields
    sys.modules["django.contrib.gis.geos"] = mock_gis.geos
    sys.modules["django.contrib.gis.measure"] = mock_gis.measure
    sys.modules["django.contrib.gis.db.models.functions"] = mock_gis.db.models.functions
    sys.modules["django.contrib.gis.forms"] = mock_gis.forms
    sys.modules["django.contrib.gis.gdal"] = mock_gis.gdal


from .base import *  # noqa: F403

# ─── Use ConsoleSMSAdapter in tests (avoid Twilio credentials) ───
DEBUG = True

# ─── SMS provider settings for tests ───
TWILIO_ACCOUNT_SID = "test"
TWILIO_AUTH_TOKEN = "test"
TWILIO_FROM_NUMBER = "+1234567890"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    app for app in INSTALLED_APPS  # noqa: F405
    if app not in ("django.contrib.gis",)
]

# ─── Disable SSL redirect for tests ───
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ─── Use simple file storage ───
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ─── Disable Redis / Celery for tests ───
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
CELERY_TASK_ALWAYS_EAGER = True

