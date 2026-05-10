"""
apps/parcels/presentation/di.py
--------------------------------
Injection de dépendances pour Sen_parcelle.
Principe SOLID (D) : les ViewSets ne créent jamais leurs dépendances —
elles les reçoivent via ce module.

En production → remplacer par un vrai conteneur IoC (dependency-injector).
"""

from functools import lru_cache


# ══════════════════════════════════════════════════════════════
# SERVICES PARTAGÉS (singletons)
# ══════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_jwt_service():
    from apps.users.application.services.jwt_service import JWTService
    return JWTService()


@lru_cache(maxsize=1)
def get_otp_service():
    from apps.users.application.services.otp_service import OTPService
    return OTPService()


@lru_cache(maxsize=1)
def get_sms_service():
    from apps.users.infrastructure.adapters.sms_adapter import get_sms_adapter
    return get_sms_adapter()


@lru_cache(maxsize=1)
def get_audit_service():
    from apps.audit.services import AuditService
    return AuditService()


@lru_cache(maxsize=1)
def get_user_repository():
    from apps.users.infrastructure.repositories import DjangoUserRepository
    return DjangoUserRepository()


@lru_cache(maxsize=1)
def get_parcel_repository():
    from apps.parcels.infrastructure.models import DjangoParcelRepository
    return DjangoParcelRepository()


def get_storage_service():
    from infrastructure.storage.s3 import S3StorageService
    return S3StorageService()


def get_notification_service():
    from apps.notifications.services.notification_service import NotificationService
    return NotificationService()


# ══════════════════════════════════════════════════════════════
# FACTORIES USE CASES — Users
# ══════════════════════════════════════════════════════════════

def get_register_uc():
    from apps.users.application.use_cases.register import RegisterUseCase
    return RegisterUseCase(
        user_repository=get_user_repository(),
        otp_service=get_otp_service(),
        sms_service=get_sms_service(),
    )


def get_login_uc():
    from apps.users.application.use_cases.login import LoginUseCase
    return LoginUseCase(
        user_repository=get_user_repository(),
        otp_service=get_otp_service(),
        jwt_service=get_jwt_service(),
        audit_service=get_audit_service(),
        sms_service=get_sms_service(),
        auth_service=get_auth_service(),
    )


def get_verify_kyc_uc():
    from apps.users.application.use_cases.verify_kyc import VerifyKYCUseCase
    return VerifyKYCUseCase(
        user_repository=get_user_repository(),
        sms_service=get_sms_service(),
        audit_service=get_audit_service(),
    )


def get_kyc_service():
    from apps.users.application.services.kyc_service import KYCService
    return KYCService(
        user_repo=get_user_repository(),
        storage_service=get_storage_service(),
        sms_service=get_sms_service(),
        notification_service=get_notification_service(),
        audit_service=get_audit_service(),
    )


def get_auth_service():
    from apps.users.application.services.auth_service import AuthService
    return AuthService(
        user_repo=get_user_repository(),
        jwt_service=get_jwt_service(),
        otp_service=get_otp_service(),
        sms_service=get_sms_service(),
        audit_service=get_audit_service(),
    )


# ══════════════════════════════════════════════════════════════
# FACTORIES USE CASES — Parcels
# ══════════════════════════════════════════════════════════════

def get_submit_parcel_uc():
    from apps.parcels.application.use_cases.submit_parcel import SubmitParcelUseCase
    return SubmitParcelUseCase(
        parcel_repo=get_parcel_repository(),
        user_repo=get_user_repository(),
        storage_service=get_storage_service(),
        notification_service=get_notification_service(),
        audit_service=get_audit_service(),
    )


def get_validate_parcel_uc():
    from apps.parcels.application.use_cases.submit_parcel import ValidateParcelUseCase
    from celery import current_app as celery_app
    return ValidateParcelUseCase(
        parcel_repo=get_parcel_repository(),
        blockchain_service=None,         # Délégué à Celery
        notification_service=get_notification_service(),
        audit_service=get_audit_service(),
        celery_app=celery_app,
    )


def get_search_parcels_uc():
    from apps.parcels.application.use_cases.submit_parcel import SearchParcelsUseCase
    return SearchParcelsUseCase(parcel_repo=get_parcel_repository())