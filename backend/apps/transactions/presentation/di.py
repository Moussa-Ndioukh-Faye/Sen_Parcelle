# ════════════════════════════════════════════════════════════════
# DI TRANSACTIONS
# apps/transactions/presentation/di.py
# ════════════════════════════════════════════════════════════════

from functools import lru_cache

from apps.parcels.presentation.di import (
    get_audit_service,
    get_notification_service,
    get_parcel_repository,
    get_user_repository,
)


@lru_cache(maxsize=1)
def get_transaction_repository():
    from apps.transactions.infrastructure.models import DjangoTransactionRepository
    return DjangoTransactionRepository()


def get_payment_factory():
    from apps.transactions.infrastructure.adapters.factory import get_payment_adapter
    return get_payment_adapter


def get_initiate_payment_uc():
    from apps.transactions.application.use_cases.payment import InitiatePaymentUseCase
    return InitiatePaymentUseCase(
        parcel_repo=get_parcel_repository(),
        user_repo=get_user_repository(),
        tx_repo=get_transaction_repository(),
        payment_factory=get_payment_factory(),
        notification_service=get_notification_service(),
        audit_service=get_audit_service(),
    )


def get_confirm_payment_uc():
    from celery import current_app as celery_app

    from apps.transactions.application.use_cases.payment import ConfirmPaymentUseCase
    return ConfirmPaymentUseCase(
        tx_repo=get_transaction_repository(),
        payment_factory=get_payment_factory(),
        notification_service=get_notification_service(),
        audit_service=get_audit_service(),
        celery_app=celery_app,
    )
