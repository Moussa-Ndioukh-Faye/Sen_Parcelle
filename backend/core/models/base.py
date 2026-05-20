"""
core/models/base.py
-------------------
BaseModel partagé par toutes les entités Django de Sen_parcelle.
- UUID comme clé primaire (évite l'énumération d'IDs)
- Timestamps automatiques
- Soft-delete (suppression logique, jamais physique)
"""

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Ajoute created_at / updated_at automatiques.
    Abstrait : jamais instancié directement.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Remplace l'auto-increment par un UUID v4.
    Raison : sécurité (pas d'énumération), distribué.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Manager par défaut : exclut les objets supprimés logiquement."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager alternatif : inclut les objets supprimés."""

    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    """
    Soft-delete : marque deleted_at au lieu de supprimer en base.
    Raison : auditabilité, conformité RGPD (on peut purger plus tard).
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects     = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Suppression logique."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        """Suppression physique (admin uniquement)."""
        super().delete()

    def restore(self):
        """Restaure un objet supprimé."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Modèle de base complet pour Sen_parcelle.
    Hérite : UUID, timestamps, soft-delete.

    Usage :
        class User(BaseModel):
            nom = models.CharField(...)
    """
    class Meta:
        abstract = True
        ordering = ['-created_at']
