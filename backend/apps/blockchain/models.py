# ═══════════════════════════════════════════════════════════════
# apps/blockchain/models.py
# Réexporte les modèles depuis infrastructure si applicable.
# Actuellement, le module blockchain utilise Celery et web3.py,
# pas de modèles Django directs. Ce fichier est requis pour que
# l'app soit reconnue par Django.
# ═══════════════════════════════════════════════════════════════

# Pas de modèles Django dans cette app (uniquement Celery tasks + services)
