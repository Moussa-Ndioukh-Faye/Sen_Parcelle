import os
from pathlib import Path

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

