# ════════════════════════════════════════════════════════════
# REPOSITORY INTERFACE (Dependency Inversion)
# apps/users/domain/repositories.py
# ════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod

from apps.users.domain.entities import UserEntity


class IUserRepository(ABC):
    """
    Interface du repository User.
    La couche domain définit le contrat,
    la couche infrastructure l'implémente.
    """

    @abstractmethod
    def get_by_id(self, user_id: str) -> UserEntity | None:
        """Retourne un utilisateur par ID ou None."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> UserEntity | None:
        """Retourne un utilisateur par email ou None."""
        ...

    @abstractmethod
    def get_by_phone(self, phone: str) -> UserEntity | None:
        """Retourne un utilisateur par téléphone ou None."""
        ...

    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity:
        """Crée ou met à jour un utilisateur."""
        ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Vérifie si un email est déjà utilisé."""
        ...

    @abstractmethod
    def exists_by_phone(self, phone: str) -> bool:
        """Vérifie si un téléphone est déjà utilisé."""
        ...

    @abstractmethod
    def set_password(self, user_id: str, password: str) -> None:
        """Définit le mot de passe d'un utilisateur."""
        ...

    @abstractmethod
    def check_password(self, user_id: str, password: str) -> bool:
        """Vérifie le mot de passe d'un utilisateur."""
        ...
