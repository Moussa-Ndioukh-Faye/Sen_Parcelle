"""
apps/audit/
-----------
Système d'audit complet pour Sen_parcelle.
- Log automatique de toutes les requêtes API sensibles
- Log manuel des actions métier importantes
- Stockage en base + Redis pour accès rapide
- Conformité RGPD (horodatage, IP, user-agent)
"""

import json
import logging
import time
from django.db import models
from django.utils import timezone
import uuid

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# MODÈLE AuditLog
# ══════════════════════════════════════════════════════════════

class AuditLog(models.Model):
    """
    Journal d'audit immuable.
    Une fois créé, jamais modifié (immutabilité = confiance).
    """

    ACTION_CHOICES = [
        # Auth
        ("login_success",    "Connexion réussie"),
        ("login_failed",     "Échec connexion"),
        ("logout",           "Déconnexion"),
        ("password_changed", "Mot de passe modifié"),
        ("2fa_enabled",      "2FA activé"),
        ("2fa_disabled",     "2FA désactivé"),
        ("account_locked",   "Compte verrouillé"),
        # KYC
        ("kyc_submitted",    "KYC soumis"),
        ("kyc_approved",     "KYC approuvé"),
        ("kyc_rejected",     "KYC rejeté"),
        # Parcelles
        ("parcel_submitted", "Parcelle soumise"),
        ("parcel_approved",  "Parcelle validée"),
        ("parcel_rejected",  "Parcelle rejetée"),
        ("parcel_certified", "Parcelle certifiée blockchain"),
        # Transactions
        ("transaction_initiated",  "Transaction initiée"),
        ("transaction_completed",  "Transaction complétée"),
        ("transaction_failed",     "Transaction échouée"),
        # Admin
        ("kyc_decision",     "Décision KYC admin"),
        ("user_suspended",   "Utilisateur suspendu"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id     = models.UUIDField(db_index=True, null=True, blank=True)
    action      = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    metadata    = models.JSONField(default=dict)       # Données contextuelles
    created_at  = models.DateTimeField(default=timezone.now, db_index=True)

    # Hash d'intégrité : garantit que le log n'a pas été altéré
    integrity_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table  = "audit_logs"
        ordering  = ["-created_at"]
        indexes   = [
            models.Index(fields=["user_id", "action"]),
            models.Index(fields=["action", "created_at"]),
        ]
        # Aucune permission de modification (immutable)
        permissions = [("view_audit_log", "Peut consulter les logs d'audit")]

    def save(self, *args, **kwargs):
        """Calcule le hash d'intégrité avant sauvegarde."""
        if not self.integrity_hash:
            self.integrity_hash = self._compute_hash()
        # Bloquer les modifications (immutabilité)
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("Les logs d'audit sont immuables.")
        super().save(*args, **kwargs)

    def _compute_hash(self) -> str:
        import hashlib
        content = f"{self.user_id}:{self.action}:{self.created_at}:{json.dumps(self.metadata, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Vérifie que le log n'a pas été altéré."""
        return self.integrity_hash == self._compute_hash()

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.user_id} → {self.action}"