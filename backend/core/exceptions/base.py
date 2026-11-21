"""
core/exceptions/base.py
-----------------------
Hiérarchie d'exceptions Sen_parcelle.
Principe : chaque couche lève ses propres exceptions,
la couche présentation les traduit en réponses HTTP.
"""

from rest_framework import status

# ══════════════════════════════════════════════════════════════
# EXCEPTIONS DOMAINE (couche domain/ — 0 dépendance HTTP)
# ══════════════════════════════════════════════════════════════


class DomainException(Exception):
    """
    Base de toutes les exceptions métier.
    Ne connaît pas HTTP — pure règle de gestion.
    """

    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundException(DomainException):
    """Entité introuvable en base."""

    def __init__(self, entity: str, identifier: str):
        super().__init__(message=f"{entity} introuvable : {identifier}", code="not_found")


class BusinessRuleViolationException(DomainException):
    """Violation d'une règle métier."""

    pass


class DuplicateEntityException(DomainException):
    """Tentative de création d'un doublon."""

    def __init__(self, entity: str, field: str):
        super().__init__(message=f"{entity} existe déjà avec ce {field}", code="duplicate")


class UnauthorizedDomainException(DomainException):
    """Action non autorisée selon les règles métier."""

    pass


# ══════════════════════════════════════════════════════════════
# EXCEPTIONS APPLICATIVES (couche application/)
# ══════════════════════════════════════════════════════════════


class ApplicationException(Exception):
    """Base des exceptions d'orchestration (use cases)."""

    def __init__(self, message: str, code: str = "application_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(ApplicationException):
    """Données d'entrée invalides."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(message="Données invalides", code="validation_error")


class ExternalServiceException(ApplicationException):
    """Erreur d'un service externe (Wave, Blockchain, SMS...)."""

    def __init__(self, service: str, detail: str):
        super().__init__(message=f"Erreur service {service}: {detail}", code="external_service_error")


# ══════════════════════════════════════════════════════════════
# EXCEPTIONS SPÉCIFIQUES AUX DOMAINES
# ══════════════════════════════════════════════════════════════


class InvalidKYCStatusException(DomainException):
    """KYC non vérifié — action refusée."""

    def __init__(self):
        super().__init__(message="Votre identité doit être vérifiée (KYC) avant cette action.", code="kyc_required")


class ParcelAlreadyCertifiedException(DomainException):
    """Parcelle déjà enregistrée sur blockchain."""

    def __init__(self, parcel_id: str):
        super().__init__(message=f"La parcelle {parcel_id} est déjà certifiée.", code="already_certified")


class ParcelFraudSuspectedException(DomainException):
    """Doublon géographique détecté — fraude probable."""

    def __init__(self, distance_m: float):
        super().__init__(
            message=f"Une parcelle similaire existe à {distance_m:.0f}m. Vérification requise.", code="fraud_suspected"
        )


class InvalidOTPException(DomainException):
    """OTP invalide ou expiré."""

    def __init__(self):
        super().__init__(message="Code OTP invalide ou expiré.", code="invalid_otp")


class PaymentFailedException(ApplicationException):
    """Paiement échoué."""

    def __init__(self, provider: str, reason: str):
        super().__init__(message=f"Paiement {provider} échoué : {reason}", code="payment_failed")


# ══════════════════════════════════════════════════════════════
# HANDLER GLOBAL DRF
# core/exceptions/handlers.py
# ══════════════════════════════════════════════════════════════

import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler global DRF.
    Traduit les exceptions domaine/applicatives en réponses HTTP.
    Format uniforme :
        {
            "error": {
                "code": "...",
                "message": "...",
                "details": {...}  ← optionnel
            }
        }
    """
    # ─── Exceptions domaine → HTTP ───
    if isinstance(exc, EntityNotFoundException):
        return Response({"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, UnauthorizedDomainException | InvalidKYCStatusException):
        return Response({"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, DuplicateEntityException):
        return Response({"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, ParcelFraudSuspectedException | BusinessRuleViolationException):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    if isinstance(exc, ValidationException):
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": exc.errors}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ExternalServiceException):
        logger.error(f"Service externe : {exc.message}")
        return Response(
            {"error": {"code": exc.code, "message": "Service temporairement indisponible."}},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if isinstance(exc, DomainException):
        return Response({"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_400_BAD_REQUEST)

    # ─── Fallback DRF standard ───
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"error": {"code": "error", "message": response.data}}
    return response
