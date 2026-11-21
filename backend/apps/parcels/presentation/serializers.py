# ══════════════════════════════════════════════════════════════
# SERIALIZERS
# apps/parcels/presentation/serializers.py
# ══════════════════════════════════════════════════════════════

from decimal import Decimal

from rest_framework import serializers


class ParcelCreateSerializer(serializers.Serializer):
    titre = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    localisation = serializers.CharField(max_length=255)
    region = serializers.ChoiceField(
        choices=[
            "Dakar",
            "Thiès",
            "Saint-Louis",
            "Ziguinchor",
            "Kaolack",
            "Diourbel",
            "Louga",
            "Fatick",
            "Kolda",
            "Tambacounda",
            "Kaffrine",
            "Matam",
            "Kédougou",
            "Sédhiou",
        ]
    )
    type_terrain = serializers.ChoiceField(choices=["residentiel", "commercial", "agricole", "industriel"])
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    superficie = serializers.FloatField(min_value=1)
    prix = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("1"))


class ParcelListSerializer(serializers.Serializer):
    id = serializers.CharField()
    titre = serializers.CharField()
    region = serializers.CharField()
    localisation = serializers.CharField()
    type_terrain = serializers.CharField()
    superficie = serializers.FloatField()
    prix = serializers.DecimalField(max_digits=14, decimal_places=2)
    status = serializers.CharField()
    owner_id = serializers.CharField()
    vendeur_nom = serializers.SerializerMethodField()

    def get_vendeur_nom(self, obj):
        # On suppose que l'objet a accès à l'entité User via le repository ou le modèle
        # Dans le cas d'une entité de domaine, il faut voir comment owner_id est résolu
        return getattr(obj, "owner_name", "Propriétaire Inconnu")


class ParcelDetailSerializer(ParcelListSerializer):
    description = serializers.CharField()
    document_hash = serializers.CharField()
    blockchain_tx_hash = serializers.CharField()
    ipfs_hash = serializers.CharField()
    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if hasattr(obj, "location") and obj.location:
            return {"latitude": obj.location.latitude, "longitude": obj.location.longitude}
        return None


class ValidateParcelSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    reason = serializers.CharField(required=False, allow_blank=True)
