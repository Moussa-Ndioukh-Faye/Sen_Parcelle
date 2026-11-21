"""
core/permissions/rbac.py
------------------------
RBAC (Role-Based Access Control) pour Sen_parcelle.
Principe : les ViewSets ne contiennent AUCUNE logique de rôle —
tout est ici, réutilisable et testable.
"""

from rest_framework.permissions import BasePermission

# ══════════════════════════════════════════════════════════════
# PERMISSIONS DE BASE PAR RÔLE
# ══════════════════════════════════════════════════════════════


class IsAcheteur(BasePermission):
    """Autorise uniquement les acheteurs authentifiés."""

    message = "Accès réservé aux acheteurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "acheteur"


class IsVendeur(BasePermission):
    """Autorise uniquement les vendeurs authentifiés."""

    message = "Accès réservé aux vendeurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "vendeur"


class IsAdmin(BasePermission):
    """Autorise uniquement les administrateurs."""

    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsVendeurOrAdmin(BasePermission):
    """Vendeur ou Admin."""

    message = "Accès réservé aux vendeurs et administrateurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("vendeur", "admin")


class IsAuthenticated(BasePermission):
    """Tout utilisateur authentifié, quel que soit son rôle."""

    message = "Authentification requise."

    def has_permission(self, request, view):
        return request.user.is_authenticated


# ══════════════════════════════════════════════════════════════
# PERMISSIONS AU NIVEAU OBJET
# ══════════════════════════════════════════════════════════════


class IsOwnerOrAdmin(BasePermission):
    """
    Autorise le propriétaire de l'objet ou un admin.
    L'objet doit avoir un attribut `owner` ou `user` ou `vendeur`.
    """

    message = "Vous n'êtes pas propriétaire de cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        # Supporte plusieurs conventions de nommage
        for attr in ("owner", "user", "vendeur", "seller"):
            if hasattr(obj, attr):
                return getattr(obj, attr) == request.user
        return False


class IsKYCVerified(BasePermission):
    """
    Vérifie que le KYC de l'utilisateur est validé.
    Requis pour : publier une parcelle, initier une transaction.
    """

    message = "Votre identité doit être vérifiée (KYC) avant cette action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.kyc_status == "verified"


class Is2FAEnabled(BasePermission):
    """
    Vérifie que le 2FA est activé.
    Requis pour les actions sensibles (validation, transfert).
    """

    message = "Le double facteur (2FA) doit être activé pour cette action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_2fa_enabled


# ══════════════════════════════════════════════════════════════
# COMBINAISONS PRÊTES À L'EMPLOI
# ══════════════════════════════════════════════════════════════


class CanPublishParcel(BasePermission):
    """
    Peut publier une parcelle :
    - Authentifié
    - Rôle : vendeur ou admin
    - KYC vérifié
    """

    message = "Publication refusée : KYC requis ou rôle insuffisant."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ("vendeur", "admin")
            and request.user.kyc_status == "verified"
        )


class CanValidateParcel(BasePermission):
    """Peut valider/certifier une parcelle : admin uniquement."""

    message = "Validation réservée aux administrateurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class CanInitiateTransaction(BasePermission):
    """
    Peut initier une transaction :
    - Authentifié
    - Rôle : acheteur
    - KYC vérifié
    - 2FA activé
    """

    message = "Transaction refusée : KYC requis et 2FA obligatoire."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "acheteur"
            and request.user.kyc_status == "verified"
            and request.user.is_2fa_enabled
        )
