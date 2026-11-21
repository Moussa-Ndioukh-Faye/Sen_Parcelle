"""
apps/users/domain/entities.py
------------------------------
Entités pures du domaine Users.
⚠️  Aucune dépendance Django ici — pure Python.
Testables sans base de données.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════


class UserRole(StrEnum):
    ACHETEUR = "acheteur"
    VENDEUR = "vendeur"
    ADMIN = "admin"


class KYCStatus(StrEnum):
    PENDING = "pending"  # En attente de vérification
    VERIFIED = "verified"  # Validé
    REJECTED = "rejected"  # Rejeté


# ══════════════════════════════════════════════════════════════
# VALUE OBJECTS (immuables, identifiés par valeur)
# ══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Email:
    """Email validé — immuable."""

    value: str

    def __post_init__(self):
        if "@" not in self.value or "." not in self.value.split("@")[-1]:
            raise ValueError(f"Email invalide : {self.value}")
        # Normalisation
        object.__setattr__(self, "value", self.value.lower().strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PhoneNumber:
    """
    Numéro de téléphone sénégalais.
    Formats acceptés : +221XXXXXXXXX ou 7XXXXXXXX
    """

    value: str

    VALID_PREFIXES = ("70", "75", "76", "77", "78")

    def __post_init__(self):
        normalized = self._normalize(self.value)
        if not self._is_valid(normalized):
            raise ValueError(f"Numéro sénégalais invalide : {self.value}")
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def _normalize(phone: str) -> str:
        digits = "".join(filter(str.isdigit, phone))
        if digits.startswith("221"):
            return f"+{digits}"
        if len(digits) == 9:
            return f"+221{digits}"
        return phone

    def _is_valid(self, phone: str) -> bool:
        if not phone.startswith("+221"):
            return False
        local = phone[4:]
        return len(local) == 9 and any(local.startswith(p) for p in self.VALID_PREFIXES)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DocumentHash:
    """Hash SHA-256 d'un document."""

    value: str

    def __post_init__(self):
        if len(self.value) != 64:
            raise ValueError("Hash SHA-256 invalide (64 caractères hexadécimaux requis)")
        if not all(c in "0123456789abcdef" for c in self.value.lower()):
            raise ValueError("Hash SHA-256 invalide (caractères non hexadécimaux)")

    def __str__(self) -> str:
        return self.value


# ══════════════════════════════════════════════════════════════
# ENTITÉ USER
# ══════════════════════════════════════════════════════════════


@dataclass
class UserEntity:
    """
    Entité User — représente les règles métier de l'utilisateur.
    Pas d'ORM ici : c'est le modèle conceptuel pur.
    """

    id: str
    nom: str
    email: Email
    telephone: PhoneNumber
    role: UserRole
    kyc_status: KYCStatus = KYCStatus.PENDING
    is_2fa_enabled: bool = False
    is_active: bool = True
    created_at: datetime | None = None

    # ─── Règles métier ───

    def can_publish_parcel(self) -> bool:
        """
        Un utilisateur peut publier une parcelle seulement si :
        - Son rôle est vendeur ou admin
        - Son KYC est vérifié
        """
        return self.role in (UserRole.VENDEUR, UserRole.ADMIN) and self.kyc_status == KYCStatus.VERIFIED

    def can_buy_parcel(self) -> bool:
        """
        Peut acheter si :
        - Rôle acheteur ou admin
        - KYC vérifié
        - 2FA activé (transaction sensible)
        """
        return (
            self.role in (UserRole.ACHETEUR, UserRole.ADMIN)
            and self.kyc_status == KYCStatus.VERIFIED
            and self.is_2fa_enabled
        )

    def can_validate_parcel(self) -> bool:
        """Seul l'admin peut certifier une parcelle."""
        return self.role == UserRole.ADMIN

    def is_kyc_verified(self) -> bool:
        return self.kyc_status == KYCStatus.VERIFIED

    def verify_kyc(self) -> "UserEntity":
        """Retourne une nouvelle entité avec KYC vérifié."""
        from dataclasses import replace

        return replace(self, kyc_status=KYCStatus.VERIFIED)

    def reject_kyc(self) -> "UserEntity":
        return replace(self, kyc_status=KYCStatus.REJECTED)

    def enable_2fa(self) -> "UserEntity":
        return replace(self, is_2fa_enabled=True)
