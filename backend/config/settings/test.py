import os
from pathlib import Path

import sys
from unittest.mock import MagicMock

# ─── Mock GDAL/GIS for environments without it (like CI or local Windows) ───
try:
    from django.contrib.gis.gdal import libgdal
except (ImportError, Exception):
    # Mocking necessary modules to prevent ImproperlyConfigured
    from unittest.mock import MagicMock
    
    from django.db import models
    class MockPointField(models.JSONField):
        def __init__(self, *args, **kwargs):
            kwargs.pop('geography', None)
            kwargs.pop('srid', None)
            super().__init__(*args, **kwargs)

    # Create a hierarchy of mocks
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



# Base settings
from .base import *  # noqa

# ─── Override DATABASES for tests (SQLite) ───
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ─── Remove PostGIS / GIS apps for tests ───
INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app not in ("django.contrib.gis",)
]

# ─── Use simple file storage ───
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ─── Disable Redis / Celery for tests ───
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
CELERY_TASK_ALWAYS_EAGER = True

