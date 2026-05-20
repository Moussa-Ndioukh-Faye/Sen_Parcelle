"""
apps/transactions/domain/entities.py
--------------------------------------
Entités pures du domaine Transaction.
Supporte Wave Sénégal et Orange Money.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class TransactionStatus(StrEnum):
    INITIATED   = "initiated"
    PENDING     = "pending"       # Paiement initié, en attente
    CONFIRMED   = "confirmed"     # Paiement confirmé par provider
    COMPLETED   = "completed"     # Propriété transférée blockchain
    FAILED      = "failed"
    CANCELLED   = "cancelled"
    REFUNDED    = "refunded"


class PaymentProvider(StrEnum):
    WAVE         = "wave"
    ORANGE_MONEY = "orange_money"


@dataclass
class TransactionEntity:
    """Entité Transaction — règles métier."""
    id:               str
    parcel_id:        str
    buyer_id:         str
    seller_id:        str
    amount_fcfa:      float
    provider:         PaymentProvider
    status:           TransactionStatus   = TransactionStatus.INITIATED
    payment_ref:      str | None       = None   # Ref. Wave/OM
    blockchain_tx:    str | None       = None   # TX Polygon
    created_at:       datetime | None  = None
    confirmed_at:     datetime | None  = None
    completed_at:     datetime | None  = None
    failure_reason:   str | None       = None

    # ─── Règles métier ───

    def can_be_confirmed(self) -> bool:
        return self.status == TransactionStatus.PENDING

    def can_be_cancelled(self) -> bool:
        return self.status in (TransactionStatus.INITIATED, TransactionStatus.PENDING)

    def is_finalized(self) -> bool:
        return self.status in (
            TransactionStatus.COMPLETED,
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
            TransactionStatus.REFUNDED,
        )

    def confirm_payment(self, payment_ref: str) -> "TransactionEntity":
        from dataclasses import replace
        return replace(
            self,
            status=TransactionStatus.CONFIRMED,
            payment_ref=payment_ref,
            confirmed_at=datetime.now(UTC),
        )

    def complete(self, blockchain_tx: str) -> "TransactionEntity":
        from dataclasses import replace
        return replace(
            self,
            status=TransactionStatus.COMPLETED,
            blockchain_tx=blockchain_tx,
            completed_at=datetime.now(UTC),
        )

    def fail(self, reason: str) -> "TransactionEntity":
        from dataclasses import replace
        return replace(self, status=TransactionStatus.FAILED, failure_reason=reason)


# ════════════════════════════════════════════════════════════════
# ADAPTER INTERFACE
# ════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod


class IPaymentAdapter(ABC):
    """Interface commune Wave / Orange Money."""

    @abstractmethod
    def initiate_payment(
        self,
        amount:      float,
        phone:       str,
        reference:   str,
        description: str,
    ) -> dict:
        """
        Initier un paiement.
        Retourne { payment_url, payment_ref, status }
        """
        ...

    @abstractmethod
    def check_status(self, payment_ref: str) -> dict:
        """
        Vérifier le statut d'un paiement.
        Retourne { status, amount, paid_at }
        """
        ...

    @abstractmethod
    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Vérifier l'authenticité d'un webhook entrant."""
        ...
