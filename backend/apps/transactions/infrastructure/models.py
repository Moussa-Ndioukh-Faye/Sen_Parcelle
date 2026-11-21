# ════════════════════════════════════════════════════════════════
# MODÈLE ORM Transaction
# apps/transactions/infrastructure/models.py
# ════════════════════════════════════════════════════════════════

from django.db import models

from apps.transactions.domain.entities import PaymentProvider, TransactionEntity, TransactionStatus
from core.models.base import BaseModel


class Transaction(BaseModel):
    """Modèle ORM Transaction."""

    STATUS_CHOICES = [(s.value, s.value) for s in TransactionStatus]
    PROVIDER_CHOICES = [(p.value, p.value) for p in PaymentProvider]

    parcel = models.ForeignKey("parcels.Parcel", on_delete=models.PROTECT, related_name="transactions")
    buyer = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="purchases")
    seller = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="sales")

    amount_fcfa = models.DecimalField(max_digits=14, decimal_places=2)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="initiated", db_index=True)
    payment_ref = models.CharField(max_length=255, blank=True, db_index=True)
    blockchain_tx = models.CharField(max_length=255, blank=True)

    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_ref"]),
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["seller", "status"]),
        ]

    def to_domain(self) -> TransactionEntity:
        return TransactionEntity(
            id=str(self.id),
            parcel_id=str(self.parcel_id),
            buyer_id=str(self.buyer_id),
            seller_id=str(self.seller_id),
            amount_fcfa=float(self.amount_fcfa),
            provider=PaymentProvider(self.provider),
            status=TransactionStatus(self.status),
            payment_ref=self.payment_ref or None,
            blockchain_tx=self.blockchain_tx or None,
            created_at=self.created_at,
            confirmed_at=self.confirmed_at,
            completed_at=self.completed_at,
            failure_reason=self.failure_reason or None,
        )

    @classmethod
    def from_domain(cls, entity: TransactionEntity) -> "Transaction":
        return cls(
            id=entity.id,
            parcel_id=entity.parcel_id,
            buyer_id=entity.buyer_id,
            seller_id=entity.seller_id,
            amount_fcfa=entity.amount_fcfa,
            provider=entity.provider.value,
            status=entity.status.value,
            payment_ref=entity.payment_ref or "",
            blockchain_tx=entity.blockchain_tx or "",
            confirmed_at=entity.confirmed_at,
            completed_at=entity.completed_at,
            failure_reason=entity.failure_reason or "",
        )


# ──────────────────────────────────────────────────────────────
# REPOSITORY DJANGO
# ──────────────────────────────────────────────────────────────


from apps.transactions.domain.repositories import ITransactionRepository


class DjangoTransactionRepository(ITransactionRepository):
    """Implémentation Django du repository Transaction."""

    def get_by_id(self, tx_id: str) -> TransactionEntity | None:
        try:
            return Transaction.objects.get(id=tx_id).to_domain()
        except Transaction.DoesNotExist:
            return None

    def get_by_payment_ref(self, payment_ref: str) -> TransactionEntity | None:
        try:
            return Transaction.objects.get(payment_ref=payment_ref).to_domain()
        except Transaction.DoesNotExist:
            return None

    def save(self, entity: TransactionEntity) -> TransactionEntity:
        tx_orm = Transaction.from_domain(entity)
        tx_orm.save()
        return tx_orm.to_domain()

    def find_by_buyer(self, buyer_id: str) -> list[TransactionEntity]:
        qs = Transaction.objects.select_related("parcel", "buyer", "seller").filter(buyer_id=buyer_id)
        return [t.to_domain() for t in qs]

    def find_by_seller(self, seller_id: str) -> list[TransactionEntity]:
        qs = Transaction.objects.select_related("parcel", "buyer", "seller").filter(seller_id=seller_id)
        return [t.to_domain() for t in qs]

    def find_by_parcel(self, parcel_id: str) -> list[TransactionEntity]:
        qs = Transaction.objects.select_related("parcel", "buyer", "seller").filter(parcel_id=parcel_id)
        return [t.to_domain() for t in qs]
