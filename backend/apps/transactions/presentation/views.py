# ════════════════════════════════════════════════════════════════
# VIEWSET TRANSACTIONS
# apps/transactions/presentation/views.py
# ════════════════════════════════════════════════════════════════

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.transactions.application.use_cases.payment import (
    ConfirmPaymentInput,
    InitiatePaymentInput,
)
from core.permissions.rbac import CanInitiateTransaction, IsAuthenticated

from .di import get_confirm_payment_uc, get_initiate_payment_uc, get_transaction_repository
from .serializers import InitiatePaymentSerializer, TransactionSerializer


class TransactionViewSet(viewsets.ViewSet):
    """
    Gestion des paiements et transactions.
    """

    def get_permissions(self):
        if self.action in ["initiate_payment"]:
            return [IsAuthenticated(), CanInitiateTransaction()]
        if self.action == "webhook":
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        """
        GET /api/transactions/
        Liste paginée des transactions (admin).
        """
        from apps.transactions.infrastructure.models import Transaction as TxORM
        qs = TxORM.objects.all().order_by("-created_at")
        page = int(request.query_params.get("page", 1))
        limit = 20
        start = (page - 1) * limit
        transactions = [t.to_domain() for t in qs[start:start+limit]]
        serializer = TransactionSerializer(transactions, many=True)
        return Response({
            "count": qs.count(),
            "page": page,
            "results": serializer.data,
        })

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=["post"], url_path="webhook/(?P<provider>[^/.]+)")
    def webhook(self, request, provider=None):
        """
        POST /api/transactions/webhook/{provider}/
        Webhook de confirmation de paiement.
        """
        if provider not in ("wave", "orange_money"):
            return Response(
                {"error": "Fournisseur inconnu"},
                status=status.HTTP_400_BAD_REQUEST
            )

        signature_header = "X-Wave-Signature" if provider == "wave" else "X-OM-Signature"
        signature = request.headers.get(signature_header, "")

        if not signature:
            return Response(
                {"error": "Signature manquante"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        payment_ref = (
            request.data.get("id") or
            request.data.get("notif_token") or
            request.data.get("data", {}).get("id", "")
        )

        if not payment_ref:
            return Response(
                {"error": "Référence de paiement manquante"},
                status=status.HTTP_400_BAD_REQUEST
            )

        uc = get_confirm_payment_uc()
        result = uc.execute(ConfirmPaymentInput(
            payment_ref=payment_ref,
            provider=provider,
            webhook_payload=request.data,
            signature=signature,
        ))

        return Response({
            "status":  result.status,
            "message": result.message,
        }, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key="user", rate="3/m", method="POST", block=True))
    @action(detail=False, methods=["post"], url_path="initier")
    def initiate_payment(self, request):
        """
        POST /api/transactions/initier/
        Initie un paiement Wave ou Orange Money.
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uc = get_initiate_payment_uc()
        result = uc.execute(InitiatePaymentInput(
            buyer_id=str(request.user.id),
            parcel_id=str(serializer.validated_data["parcel_id"]),
            provider=serializer.validated_data["provider"],
        ))

        return Response({
            "transaction_id": result.transaction_id,
            "payment_url":    result.payment_url,
            "amount":         result.amount_fcfa,
            "provider":       result.provider,
            "message":        result.message,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="mes-achats")
    def my_purchases(self, request):
        """Liste les achats de l'utilisateur connecté."""
        repo = get_transaction_repository()
        transactions = repo.find_by_buyer(str(request.user.id))
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="mes-ventes")
    def my_sales(self, request):
        """Liste les ventes de l'utilisateur connecté."""
        repo = get_transaction_repository()
        transactions = repo.find_by_seller(str(request.user.id))
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
