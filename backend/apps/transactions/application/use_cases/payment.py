"""
apps/transactions/application/use_cases/
-----------------------------------------
UC: InitiatePayment, ConfirmPayment, HandleWebhook, TransferOwnership
"""

import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# UC: Initier un paiement
# ════════════════════════════════════════════════════════════════

@dataclass
class InitiatePaymentInput:
    buyer_id:    str
    parcel_id:   str
    provider:    str      # "wave" | "orange_money"


@dataclass
class InitiatePaymentOutput:
    transaction_id: str
    payment_url:    str
    payment_ref:    str
    amount_fcfa:    float
    provider:       str
    message:        str


class InitiatePaymentUseCase:
    """
    UC: L'acheteur initie un achat de parcelle.

    Flux :
    1. Vérifier parcelle certifiée + acheteur KYC + 2FA
    2. Créer la transaction en base
    3. Appeler Wave ou Orange Money API
    4. Retourner l'URL de paiement
    """

    def __init__(self, parcel_repo, user_repo, tx_repo,
                 payment_factory, notification_service, audit_service):
        self._parcels       = parcel_repo
        self._users         = user_repo
        self._transactions  = tx_repo
        self._payment       = payment_factory
        self._notify        = notification_service
        self._audit         = audit_service

    def execute(self, data: InitiatePaymentInput) -> InitiatePaymentOutput:
        from apps.transactions.domain.entities import (
            PaymentProvider,
            TransactionEntity,
            TransactionStatus,
        )
        from core.exceptions.base import (
            BusinessRuleViolationException,
            EntityNotFoundException,
            InvalidKYCStatusException,
        )

        # ─── Vérifier l'acheteur ───
        buyer = self._users.get_by_id(data.buyer_id)
        if buyer is None:
            raise EntityNotFoundException("Utilisateur", data.buyer_id)

        if not buyer.can_buy_parcel():
            raise InvalidKYCStatusException()

        # ─── Vérifier la parcelle ───
        parcel = self._parcels.get_by_id(data.parcel_id)
        if parcel is None:
            raise EntityNotFoundException("Parcelle", data.parcel_id)

        if not parcel.can_be_purchased():
            raise BusinessRuleViolationException(
                "Cette parcelle n'est pas disponible à l'achat.",
                "parcel_not_available"
            )

        if parcel.owner_id == data.buyer_id:
            raise BusinessRuleViolationException(
                "Vous ne pouvez pas acheter votre propre parcelle.",
                "self_purchase"
            )

        # ─── Créer la transaction ───
        reference = f"SPN-{str(uuid.uuid4())[:8].upper()}"
        tx = TransactionEntity(
            id=str(uuid.uuid4()),
            parcel_id=data.parcel_id,
            buyer_id=data.buyer_id,
            seller_id=parcel.owner_id,
            amount_fcfa=parcel.prix,
            provider=PaymentProvider(data.provider),
            status=TransactionStatus.INITIATED,
        )
        self._transactions.save(tx)

        # ─── Initier le paiement ───
        adapter  = self._payment(data.provider)
        pay_result = adapter.initiate_payment(
            amount=parcel.prix,
            phone=str(buyer.telephone),
            reference=reference,
            description=f"Sen_parcelle : {parcel.titre} · {parcel.region}",
        )

        # Mettre à jour avec la référence paiement
        tx.payment_ref = pay_result["payment_ref"]
        self._transactions.save(tx)

        # ─── Notifier le vendeur ───
        self._notify.notify_user(
            parcel.owner_id,
            "purchase_initiated",
            {"parcel_titre": parcel.titre, "buyer_nom": buyer.nom}
        )

        # ─── Audit ───
        self._audit.log(data.buyer_id, "transaction_initiated", {
            "transaction_id": tx.id,
            "parcel_id":      data.parcel_id,
            "amount":         parcel.prix,
            "provider":       data.provider,
        })

        return InitiatePaymentOutput(
            transaction_id=tx.id,
            payment_url=pay_result["payment_url"],
            payment_ref=pay_result["payment_ref"],
            amount_fcfa=parcel.prix,
            provider=data.provider,
            message=f"Paiement {data.provider} initié. Complétez sur l'URL fournie.",
        )


# ════════════════════════════════════════════════════════════════
# UC: Confirmer un paiement (après webhook)
# ════════════════════════════════════════════════════════════════

@dataclass
class ConfirmPaymentInput:
    payment_ref:  str
    provider:     str
    webhook_payload: dict
    signature:    str


@dataclass
class ConfirmPaymentOutput:
    transaction_id: str
    status:         str
    message:        str


class ConfirmPaymentUseCase:
    """
    UC: Webhook du provider confirme le paiement.

    Flux :
    1. Vérifier signature webhook (sécurité)
    2. Récupérer la transaction
    3. Confirmer le paiement
    4. Déclencher le transfert de propriété (Celery async)
    5. Notifier acheteur + vendeur
    """

    def __init__(self, tx_repo, payment_factory,
                 notification_service, audit_service, celery_app):
        self._transactions = tx_repo
        self._payment      = payment_factory
        self._notify       = notification_service
        self._audit        = audit_service
        self._celery       = celery_app

    def execute(self, data: ConfirmPaymentInput) -> ConfirmPaymentOutput:
        from core.exceptions.base import BusinessRuleViolationException, EntityNotFoundException

        # ─── Vérifier la signature webhook ───
        adapter = self._payment(data.provider)
        if not adapter.verify_webhook(data.webhook_payload, data.signature):
            logger.warning(f"Webhook signature invalide : provider={data.provider}")
            raise BusinessRuleViolationException(
                "Signature webhook invalide.", "invalid_webhook_signature"
            )

        # ─── Récupérer la transaction ───
        tx = self._transactions.get_by_payment_ref(data.payment_ref)
        if tx is None:
            raise EntityNotFoundException("Transaction", data.payment_ref)

        if tx.is_finalized():
            return ConfirmPaymentOutput(
                transaction_id=tx.id,
                status=tx.status.value,
                message="Transaction déjà traitée.",
            )

        # ─── Vérifier le statut chez le provider ───
        status_info = adapter.check_status(data.payment_ref)

        if status_info["status"] == "confirmed":
            confirmed_tx = tx.confirm_payment(data.payment_ref)
            self._transactions.save(confirmed_tx)

            # ─── Déclencher transfert propriété (Celery async) ───
            self._celery.send_task(
                "blockchain.transfer_ownership",
                kwargs={
                    "transaction_id": tx.id,
                    "parcel_id":      tx.parcel_id,
                    "seller_id":      tx.seller_id,
                    "buyer_id":       tx.buyer_id,
                }
            )

            # ─── Notifications ───
            self._notify.notify_user(tx.buyer_id, "payment_confirmed", {
                "transaction_id": tx.id, "amount": tx.amount_fcfa
            })
            self._notify.notify_user(tx.seller_id, "payment_received", {
                "transaction_id": tx.id, "amount": tx.amount_fcfa
            })

            self._audit.log(tx.buyer_id, "transaction_completed", {
                "transaction_id": tx.id,
                "parcel_id":      tx.parcel_id,
            })

            return ConfirmPaymentOutput(
                transaction_id=tx.id,
                status="confirmed",
                message="Paiement confirmé. Transfert de propriété en cours.",
            )

        elif status_info["status"] in ("failed", "cancelled"):
            failed_tx = tx.fail(f"Provider: {status_info['status']}")
            self._transactions.save(failed_tx)
            return ConfirmPaymentOutput(
                transaction_id=tx.id,
                status="failed",
                message="Paiement échoué.",
            )

        return ConfirmPaymentOutput(
            transaction_id=tx.id,
            status="pending",
            message="Paiement en attente de confirmation.",
        )
