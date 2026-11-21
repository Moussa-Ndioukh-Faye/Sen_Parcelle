# ══════════════════════════════════════════════════════════════
# REPOSITORY DJANGO (implémente IUserRepository)
# apps/users/infrastructure/repositories.py
# ══════════════════════════════════════════════════════════════


from apps.users.domain.entities import UserEntity
from apps.users.domain.repositories import IUserRepository

from .models import User


class DjangoUserRepository(IUserRepository):
    """
    Implémentation Django du repository User.
    Isole complètement l'ORM du domaine.
    """

    def get_by_id(self, user_id: str) -> UserEntity | None:
        try:
            return User.objects.select_related("kyc_verified_by").get(id=user_id).to_domain()
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> UserEntity | None:
        try:
            return User.objects.select_related("kyc_verified_by").get(email__iexact=email).to_domain()
        except User.DoesNotExist:
            return None

    def get_by_phone(self, phone: str) -> UserEntity | None:
        try:
            return User.objects.select_related("kyc_verified_by").get(telephone=phone).to_domain()
        except User.DoesNotExist:
            return None

    def save(self, entity: UserEntity) -> UserEntity:
        user, _ = User.objects.update_or_create(
            id=entity.id,
            defaults={
                "nom": entity.nom,
                "email": str(entity.email),
                "telephone": str(entity.telephone),
                "role": entity.role.value,
                "kyc_status": entity.kyc_status.value,
                "is_2fa_enabled": entity.is_2fa_enabled,
                "is_active": entity.is_active,
            },
        )
        return user.to_domain()

    def exists_by_email(self, email: str) -> bool:
        return User.objects.filter(email__iexact=email).exists()

    def exists_by_phone(self, phone: str) -> bool:
        return User.objects.filter(telephone=phone).exists()

    def set_password(self, user_id: str, password: str) -> None:
        user = User.objects.get(id=user_id)
        user.set_password(password)
        user.save()

    def check_password(self, user_id: str, password: str) -> bool:
        try:
            user = User.objects.get(id=user_id)
            return user.check_password(password)
        except User.DoesNotExist:
            return False
