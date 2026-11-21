"""
apps/parcels/presentation/views.py
----------------------------------
ViewSets DRF pour la gestion des parcelles.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.parcels.application.use_cases.submit_parcel import (
    SearchParcelsInput,
    SubmitParcelInput,
    ValidateParcelInput,
)
from core.permissions.rbac import CanPublishParcel, CanValidateParcel, IsAuthenticated

from .di import get_search_parcels_uc, get_submit_parcel_uc, get_validate_parcel_uc
from .serializers import (
    ParcelCreateSerializer,
    ParcelDetailSerializer,
    ParcelListSerializer,
    ValidateParcelSerializer,
)


class ParcelViewSet(viewsets.ViewSet):
    """
    CRUD Parcelles + actions admin.

    Permissions par action :
    - list/retrieve  → public
    - create         → vendeur + KYC vérifié
    - valider        → admin uniquement
    """

    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action == "create":
            return [CanPublishParcel()]
        if self.action == "valider":
            return [CanValidateParcel()]
        return [IsAuthenticated()]

    def list(self, request):
        """
        GET /api/parcelles/
        Recherche avec filtres : région, prix, superficie, type_terrain, géo.
        """
        uc = get_search_parcels_uc()
        result = uc.execute(
            SearchParcelsInput(
                region=request.query_params.get("region"),
                min_prix=request.query_params.get("min_prix") or request.query_params.get("min_price"),
                max_prix=request.query_params.get("max_prix") or request.query_params.get("max_price"),
                min_superficie=request.query_params.get("min_superficie") or request.query_params.get("min_surface"),
                type_terrain=request.query_params.get("type_terrain"),
                latitude=request.query_params.get("latitude"),
                longitude=request.query_params.get("longitude"),
                radius_km=request.query_params.get("radius_km"),
                status=request.query_params.get("status", "certified"),
                page=int(request.query_params.get("page", 1)),
            )
        )

        serializer = ParcelListSerializer(result.parcels, many=True)
        return Response(
            {
                "count": result.total,
                "page": result.page,
                "results": serializer.data,
            }
        )

    def retrieve(self, request, pk=None):
        """GET /api/parcelles/{id}/"""
        from apps.parcels.infrastructure.models import DjangoParcelRepository

        repo = DjangoParcelRepository()
        parcel = repo.get_by_id(pk)
        if not parcel:
            return Response(
                {"error": {"code": "not_found", "message": "Parcelle introuvable"}}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ParcelDetailSerializer(parcel).data)

    def create(self, request):
        """
        POST /api/parcelles/
        Upload multipart : champs + document.
        """
        serializer = ParcelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = request.FILES.get("document")
        if not document:
            return Response(
                {"error": {"code": "missing_document", "message": "Document requis"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uc = get_submit_parcel_uc()
        result = uc.execute(
            SubmitParcelInput(
                owner_id=str(request.user.id),
                document_bytes=document.read(),
                document_name=document.name,
                **serializer.validated_data,
            )
        )

        return Response(
            {
                "parcel_id": result.parcel_id,
                "status": result.status,
                "document_hash": result.document_hash,
                "message": result.message,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        """POST /api/parcelles/{id}/valider/ — Admin."""
        serializer = ValidateParcelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uc = get_validate_parcel_uc()
        result = uc.execute(
            ValidateParcelInput(
                parcel_id=pk,
                admin_id=str(request.user.id),
                decision=serializer.validated_data["decision"],
                reason=serializer.validated_data.get("reason", ""),
            )
        )

        return Response(
            {
                "parcel_id": result.parcel_id,
                "status": result.status,
                "blockchain_hash": result.blockchain_hash,
                "message": result.message,
            }
        )

    @action(detail=False, methods=["get"], url_path="mes-parcelles")
    def mes_parcelles(self, request):
        """GET /api/parcelles/mes-parcelles/ — Parcelles du vendeur."""
        from apps.parcels.infrastructure.models import DjangoParcelRepository

        repo = DjangoParcelRepository()
        parcels = repo.find_by_owner(str(request.user.id))
        return Response(ParcelListSerializer(parcels, many=True).data)
