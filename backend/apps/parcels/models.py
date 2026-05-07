# ═══════════════════════════════════════════════════════════════
# apps/parcels/models.py
# Réexporte les modèles depuis infrastructure pour que Django
# puisse les détecter et créer les migrations.
# ═══════════════════════════════════════════════════════════════

from apps.parcels.infrastructure.models import Parcel, ParcelPhoto  # noqa: F401
