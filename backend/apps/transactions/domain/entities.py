"""
apps/transactions/domain/entities.py
--------------------------------------
Entités pures du domaine Transaction.
Supporte Wave Sénégal et Orange Money.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class TransactionStatus(str, Enum):
    INITIATED   = "initiated"
    PENDING     = "pending"       # Paiement initié, en attente
    CONFIRMED   = "confirmed"     # Paiement confirmé par provider
    COMPLETED   = "completed"     # Propriété transférée blockchain
    FAILED      = "failed"
    CANCELLED   = "cancelled"
    REFUNDED    = "refunded"


class PaymentProvider(str, Enum):
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
    payment_ref:      Optional[str]       = None   # Ref. Wave/OM
    blockchain_tx:    Optional[str]       = None   # TX Polygon
    created_at:       Optional[datetime]  = None
    confirmed_at:     Optional[datetime]  = None
    completed_at:     Optional[datetime]  = None
    failure_reason:   Optional[str]       = None

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
        from datetime import timezone
        return replace(
            self,
            status=TransactionStatus.CONFIRMED,
            payment_ref=payment_ref,
            confirmed_at=datetime.now(timezone.utc),
        )

    def complete(self, blockchain_tx: str) -> "TransactionEntity":
        from dataclasses import replace
        from datetime import timezone
        return replace(
            self,
            status=TransactionStatus.COMPLETED,
            blockchain_tx=blockchain_tx,
            completed_at=datetime.now(timezone.utc),
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