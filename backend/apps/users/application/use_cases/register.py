"""
apps/users/application/use_cases/register.py
--------------------------------------------
Use Case : Inscription d'un nouvel utilisateur.
Orchestre : validation → création → OTP SMS → retour.
"""

import uuid
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

from apps.users.domain.entities import (
    UserEntity, Email, PhoneNumber, UserRole, KYCStatus,
)
from apps.users.domain.repositories import IUserRepository
from core.exceptions.base import (
    DuplicateEntityException, ValidationException
)


@dataclass
class RegisterInput:
    """DTO d'entrée pour l'inscription."""
    nom:       str
    email:     str
    telephone: str
    password:  str
    role:      str = "acheteur"


@dataclass
class RegisterOutput:
    """DTO de sortie après inscription réussie."""
    user_id:   str
    message:   str
    otp_sent:  bool


class RegisterUseCase:
    """
    UC: Inscription utilisateur.

    Règles métier :
    1. Email unique
    2. Téléphone unique et valide (format SN)
    3. Mot de passe min 8 caractères
    4. OTP envoyé après inscription pour vérifier le téléphone
    """

    def __init__(self, user_repository: IUserRepository, otp_service, sms_service):
        self._users = user_repository
        self._otp   = otp_service
        self._sms   = sms_service

    def execute(self, data: RegisterInput) -> RegisterOutput:
        # ─── 1. Validation des value objects ───
        try:
            email     = Email(data.email)
            telephone = PhoneNumber(data.telephone)
        except ValueError as e:
            raise ValidationException({"field": str(e)})

        # ─── 2. Unicité ───
        if self._users.exists_by_email(str(email)):
            raise DuplicateEntityException("Utilisateur", "email")

        if self._users.exists_by_phone(str(telephone)):
            raise DuplicateEntityException("Utilisateur", "téléphone")

        # ─── 3. Validation mot de passe ───
        if len(data.password) < 8:
            raise ValidationException({"password": "Minimum 8 caractères requis."})

        # ─── 4. Création entité ───
        user_entity = UserEntity(
            id=str(uuid.uuid4()),
            nom=data.nom.strip(),
            email=email,
            telephone=telephone,
            role=UserRole(data.role),
            kyc_status=KYCStatus.PENDING,
            is_2fa_enabled=False,
            is_active=True,
        )

        # ─── 5. Persistance (via repository) avec transaction ───
        from django.db import transaction
        with transaction.atomic():
            saved_user = self._users.save(user_entity)
            # On délègue le hachage du mot de passe à l'infrastructure
            self._users.set_password(user_entity.id, data.password)

        # ─── 6. Envoi OTP SMS ───
        otp_sent = False
        try:
            otp_code = self._otp.generate(user_entity.id, purpose="verification")
            self._sms.send(
                to=str(telephone),
                message=f"Sen_parcelle : votre code de vérification est {otp_code}. Valable 5 minutes."
            )
            otp_sent = True
        except Exception as e:
            logger.warning(f"Échec envoi OTP SMS inscription user={user_entity.id}: {e}")

        return RegisterOutput(
            user_id=saved_user.id,
            message="Compte créé avec succès. Vérifiez votre téléphone.",
            otp_sent=otp_sent,
        )