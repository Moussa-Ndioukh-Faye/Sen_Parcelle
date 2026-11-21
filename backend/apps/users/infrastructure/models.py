"""
apps/users/infrastructure/models.py
------------------------------------
Modèle ORM Django — couche infrastructure.
Ce fichier connaît Django mais le domaine ne le connaît pas.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.users.domain.entities import Email, KYCStatus, PhoneNumber, UserEntity, UserRole
from core.models.base import SoftDeleteModel, TimeStampedModel

# ══════════════════════════════════════════════════════════════
# MANAGER PERSONNALISÉ
# ══════════════════════════════════════════════════════════════


class SenParcelleUserManager(BaseUserManager):
    """Manager pour le modèle User personnalisé."""

    def create_user(self, email: str, telephone: str, password: str, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        if not telephone:
            raise ValueError("Le téléphone est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, telephone=telephone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, telephone: str, password: str, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, telephone, password, **extra_fields)


# ══════════════════════════════════════════════════════════════
# MODÈLE USER
# ══════════════════════════════════════════════════════════════


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel, SoftDeleteModel):
    """
    Modèle User Sen_parcelle.
    - UUID comme PK
    - Email comme identifiant (pas de username)
    - KYC + 2FA intégrés
    - Soft-delete
    """

    ROLE_CHOICES = [
        ("acheteur", "Acheteur"),
        ("vendeur", "Vendeur"),
        ("admin", "Administrateur"),
    ]

    KYC_CHOICES = [
        ("pending", "En attente"),
        ("verified", "Vérifié"),
        ("rejected", "Rejeté"),
    ]

    # ─── Identité ───
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, verbose_name="Nom complet")
    email = models.EmailField(unique=True, db_index=True)
    telephone = models.CharField(max_length=20, unique=True, db_index=True)

    # ─── Rôle & Statut ───
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="acheteur", db_index=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_CHOICES, default="pending", db_index=True)

    # ─── Sécurité ───
    is_2fa_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True)  # TOTP secret chiffré
    failed_attempts = models.PositiveSmallIntegerField(default=0)  # Brute force protection
    locked_until = models.DateTimeField(null=True, blank=True)  # Lockout temporaire

    # ─── Django internals ───
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # ─── Documents KYC ───
    kyc_document_hash = models.CharField(max_length=64, blank=True)  # SHA-256 CNI
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    kyc_verified_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="kyc_validations"
    )

    objects = SenParcelleUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "telephone"]

    class Meta:
        db_table = "users"
        verbose_name = "Utilisateur"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["kyc_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.nom} <{self.email}> [{self.role}]"

    # ─── Mapping vers entité domaine ───
    def to_domain(self) -> UserEntity:
        """
        Convertit l'ORM en entité domaine pure.
        Point de sortie de la couche infrastructure vers le domaine.
        """
        return UserEntity(
            id=str(self.id),
            nom=self.nom,
            email=Email(self.email),
            telephone=PhoneNumber(self.telephone),
            role=UserRole(self.role),
            kyc_status=KYCStatus(self.kyc_status),
            is_2fa_enabled=self.is_2fa_enabled,
            is_active=self.is_active,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: UserEntity) -> "User":
        """
        Construit un ORM depuis une entité domaine.
        Point d'entrée de la couche infrastructure depuis le domaine.
        """
        return cls(
            id=entity.id,
            nom=entity.nom,
            email=str(entity.email),
            telephone=str(entity.telephone),
            role=entity.role.value,
            kyc_status=entity.kyc_status.value,
            is_2fa_enabled=entity.is_2fa_enabled,
            is_active=entity.is_active,
        )


# ══════════════════════════════════════════════════════════════
# MODÈLE OTP (codes SMS temporaires)
# ══════════════════════════════════════════════════════════════


class OTPCode(TimeStampedModel):
    """
    Codes OTP SMS pour le 2FA.
    - Durée de vie : 5 minutes
    - Usage unique
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6)  # 6 chiffres
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    purpose = models.CharField(max_length=30, default="login")  # login | transaction | kyc

    class Meta:
        db_table = "otp_codes"
        indexes = [models.Index(fields=["user", "is_used", "expires_at"])]

    def is_valid(self) -> bool:
        from django.utils import timezone

        return not self.is_used and self.expires_at > timezone.now()
