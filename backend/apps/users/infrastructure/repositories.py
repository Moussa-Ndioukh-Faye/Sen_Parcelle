# ══════════════════════════════════════════════════════════════
# REPOSITORY DJANGO (implémente IUserRepository)
# apps/users/infrastructure/repositories.py
# ══════════════════════════════════════════════════════════════

from typing import Optional, List
from apps.users.domain.entities import UserEntity
from apps.users.domain.repositories import IUserRepository
from .models import User


class DjangoUserRepository(IUserRepository):
    """
    Implémentation Django du repository User.
    Isole complètement l'ORM du domaine.
    """

    def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        try:
            return User.objects.get(id=user_id).to_domain()
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        try:
            return User.objects.get(email=email.lower()).to_domain()
        except User.DoesNotExist:
            return None

    def get_by_phone(self, phone: str) -> Optional[UserEntity]:
        try:
            return User.objects.get(telephone=phone).to_domain()
        except User.DoesNotExist:
            return None

    def save(self, entity: UserEntity) -> UserEntity:
        user, _ = User.objects.update_or_create(
            id=entity.id,
            defaults={
                "nom":           entity.nom,
                "email":         str(entity.email),
                "telephone":     str(entity.telephone),
                "role":          entity.role.value,
                "kyc_status":    entity.kyc_status.value,
                "is_2fa_enabled": entity.is_2fa_enabled,
                "is_active":     entity.is_active,
            }
        )
        return user.to_domain()

    def exists_by_email(self, email: str) -> bool:
        return User.objects.filter(email=email.lower()).exists()

    def exists_by_phone(self, phone: str) -> bool:
        return User.objects.filter(telephone=phone).exists()