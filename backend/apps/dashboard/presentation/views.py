import logging

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        from apps.parcels.infrastructure.models import Parcel as ParcelORM
        from apps.transactions.infrastructure.models import Transaction as TxORM
        from apps.users.infrastructure.models import User as UserORM

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        parcels = ParcelORM.objects
        users = UserORM.objects
        txs = TxORM.objects

        total_parcelles = parcels.count()
        parcelles_certifiees = parcels.filter(status="certified").count()
        parcelles_en_attente = parcels.filter(status="pending").count()
        parcelles_rejetees = parcels.filter(status="rejected").count()

        total_users = users.count()
        kyc_pending = users.filter(kyc_status="pending").count()
        kyc_verified = users.filter(kyc_status="verified").count()

        transactions_mois = txs.filter(created_at__gte=month_start).count()
        volume_fcfa = txs.filter(status="completed").aggregate(Sum("amount_fcfa"))["amount_fcfa__sum"] or 0

        return Response(
            {
                "parcelles": {
                    "total": total_parcelles,
                    "certifiees": parcelles_certifiees,
                    "en_attente": parcelles_en_attente,
                    "rejetees": parcelles_rejetees,
                },
                "utilisateurs": {
                    "total": total_users,
                    "kyc_pending": kyc_pending,
                    "kyc_verified": kyc_verified,
                },
                "transactions": {
                    "mois": transactions_mois,
                    "volume_fcfa": volume_fcfa,
                },
                "blockchain": {
                    "total_certified": parcelles_certifiees,
                },
            }
        )
