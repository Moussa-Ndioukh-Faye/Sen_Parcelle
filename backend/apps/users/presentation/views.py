"""
apps/users/presentation/views.py
----------------------------------
ViewSets DRF pour l'authentification et la gestion des utilisateurs.
"""
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.parcels.presentation.di import get_login_uc, get_register_uc, get_verify_kyc_uc
from apps.users.application.use_cases.login import LoginInput
from apps.users.application.use_cases.register import RegisterInput
from apps.users.application.use_cases.verify_kyc import VerifyKYCInput
from core.permissions.rbac import IsAdmin, IsAuthenticated

from .serializers import LoginSerializer, RegisterSerializer


class AuthViewSet(viewsets.ViewSet):
    """
    Endpoints d'authentification.
    Aucune permission requise (public).
    """
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="3/m", method="POST", block=True))
    @action(detail=False, methods=["post"], url_path="inscription")
    def register(self, request):
        """
        POST /api/auth/inscription/
        Crée un compte utilisateur.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uc = get_register_uc()
        result = uc.execute(RegisterInput(**serializer.validated_data))

        return Response({
            "user_id":  result.user_id,
            "message":  result.message,
            "otp_sent": result.otp_sent,
        }, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        """
        POST /api/auth/login/
        Connexion + 2FA OTP.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uc = get_login_uc()
        result = uc.execute(LoginInput(**serializer.validated_data))

        if result.requires_otp:
            return Response({
                "requires_otp": True,
                "user_id": result.user_id,
                "message": "Code OTP envoyé par SMS.",
            }, status=status.HTTP_200_OK)

        return Response({
            "access_token":  result.access_token,
            "refresh_token": result.refresh_token,
            "user_id":       result.user_id,
            "role":          result.role,
        }, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="moi")
    def me(self, request):
        """GET /api/utilisateurs/moi/"""
        user = request.user
        return Response({
            "id":             str(user.id),
            "nom":            user.nom,
            "email":          user.email,
            "telephone":      user.telephone,
            "role":           user.role,
            "kyc_status":     user.kyc_status,
            "is_2fa_enabled": user.is_2fa_enabled,
        })

    @action(detail=True, methods=["post"], url_path="kyc", permission_classes=[IsAdmin])
    def verify_kyc(self, request, pk=None):
        """POST /api/utilisateurs/{id}/kyc/ — Admin valide le KYC."""
        uc = get_verify_kyc_uc()
        result = uc.execute(VerifyKYCInput(
            user_id=pk,
            admin_id=str(request.user.id),
            decision=request.data.get("decision"),
            reason=request.data.get("reason", ""),
        ))
        return Response({
            "user_id":    result.user_id,
            "kyc_status": result.kyc_status,
            "message":    result.message,
        })
