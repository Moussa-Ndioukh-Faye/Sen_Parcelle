import logging

from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class BlockchainViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="info")
    def info(self, request):
        try:
            from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
            adapter = PolygonAdapter()
            return Response({
                "chainId": adapter._w3.eth.chain_id,
                "contractAddress": settings.POLYGON_CONTRACT_ADDRESS,
                "lastBlock": adapter._w3.eth.block_number,
                "network": "Mumbai" if adapter._w3.eth.chain_id == 80001 else "Polygon",
            })
        except Exception as e:
            logger.warning(f"Blockchain info unavailable: {e}")
            return Response({
                "chainId": settings.POLYGON_CHAIN_ID,
                "contractAddress": settings.POLYGON_CONTRACT_ADDRESS,
                "lastBlock": 0,
                "network": "Unavailable",
            })

    @action(detail=False, methods=["get"], url_path="verify/(?P<hash>[^/.]+)")
    def verify(self, request, hash=None):
        if not hash or len(hash) < 10:
            return Response({"verified": False, "error": "Hash invalide"}, status=400)
        try:
            from apps.blockchain.infrastructure.adapters.polygon_adapter import PolygonAdapter
            adapter = PolygonAdapter()
            result = adapter.verify_certificate(hash)
            return Response({
                "verified": result["valide"],
                "parcel_id": result.get("parcel_id"),
                "owner": result.get("owner"),
                "timestamp": result.get("date_enregistrement"),
            })
        except Exception as e:
            logger.warning(f"Verify failed: {e}")
            return Response({"verified": False, "error": str(e)})

    @action(detail=False, methods=["get"], url_path="balance")
    def balance(self, request):
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
            balance_wei = w3.eth.get_balance(settings.POLYGON_CONTRACT_ADDRESS)
            return Response({
                "wei": str(balance_wei),
                "eth": str(w3.from_wei(balance_wei, "ether")),
            })
        except Exception as e:
            logger.warning(f"Balance check failed: {e}")
            return Response({"wei": "0", "eth": "0"})

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        from apps.parcels.infrastructure.models import Parcel as ParcelORM
        certified = ParcelORM.objects.filter(status="certified").count()
        pending = ParcelORM.objects.filter(status="pending").count()
        return Response({
            "certified_parcels": certified,
            "pending_parcels": pending,
            "total_tx": certified,
        })


class AuditViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="recent")
    def recent(self, request):
        from apps.audit.services import AuditService
        limit = int(request.query_params.get("limit", 20))
        events = AuditService().get_recent_events(limit=limit)
        return Response(events)

    @action(detail=False, methods=["get"], url_path="user/(?P<user_id>[^/.]+)")
    def user_history(self, request, user_id=None):
        from apps.audit.services import AuditService
        events = AuditService().get_user_history(user_id)
        return Response(events)

    @action(detail=False, methods=["get"], url_path="security")
    def security_events(self, request):
        from apps.audit.services import AuditService
        events = AuditService().get_security_events()
        return Response(events)


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="preferences")
    def preferences(self, request):
        user = request.user
        return Response({
            "sms": getattr(user, "notify_sms", True),
            "email": getattr(user, "notify_email", True),
            "push": getattr(user, "notify_push", True),
        })

    @action(detail=False, methods=["post"], url_path="preferences")
    def update_preferences(self, request):
        user = request.user
        for key in ("sms", "email", "push"):
            if key in request.data:
                setattr(user, f"notify_{key}", bool(request.data[key]))
        user.save(update_fields=[f"notify_{k}" for k in ("sms", "email", "push") if k in request.data])
        return Response({"status": "ok"})

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        from apps.notifications.models import NotificationLog
        limit = int(request.query_params.get("limit", 20))
        logs = NotificationLog.objects.filter(user=request.user).order_by("-created_at")[:limit]
        return Response([
            {
                "id": str(log.id), "event": log.event, "channel": log.channel,
                "read": log.read, "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ])
