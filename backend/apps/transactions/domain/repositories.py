# ════════════════════════════════════════════════════════════════
# REPOSITORY INTERFACE
# apps/transactions/domain/repositories.py
# ════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import TransactionEntity


class ITransactionRepository(ABC):
    """Interface du repository Transaction."""

    @abstractmethod
    def get_by_id(self, tx_id: str) -> Optional[TransactionEntity]:
        """Retourne une transaction par ID."""
        ...

    @abstractmethod
    def get_by_payment_ref(self, payment_ref: str) -> Optional[TransactionEntity]:
        """Retourne une transaction par sa référence de paiement (Wave/OM)."""
        ...

    @abstractmethod
    def save(self, transaction: TransactionEntity) -> TransactionEntity:
        """Crée ou met à jour une transaction."""
        ...

    @abstractmethod
    def find_by_buyer(self, buyer_id: str) -> List[TransactionEntity]:
        """Liste les transactions d'un acheteur."""
        ...

    @abstractmethod
    def find_by_seller(self, seller_id: str) -> List[TransactionEntity]:
        """Liste les transactions d'un vendeur."""
        ...

    @abstractmethod
    def find_by_parcel(self, parcel_id: str) -> List[TransactionEntity]:
        """Liste les transactions liées à une parcelle."""
        ...
