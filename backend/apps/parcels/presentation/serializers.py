# ══════════════════════════════════════════════════════════════
# SERIALIZERS
# apps/parcels/presentation/serializers.py
# ══════════════════════════════════════════════════════════════

from rest_framework import serializers


class ParcelCreateSerializer(serializers.Serializer):
    titre       = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    region      = serializers.ChoiceField(choices=[
        "Dakar","Thiès","Saint-Louis","Ziguinchor","Kaolack",
        "Diourbel","Louga","Fatick","Kolda","Tambacounda",
        "Kaffrine","Matam","Kédougou","Sédhiou"
    ])
    latitude    = serializers.FloatField(min_value=-90, max_value=90)
    longitude   = serializers.FloatField(min_value=-180, max_value=180)
    surface     = serializers.FloatField(min_value=1)
    price       = serializers.FloatField(min_value=1)


class ParcelListSerializer(serializers.Serializer):
    id       = serializers.CharField()
    titre    = serializers.CharField()
    region   = serializers.CharField()
    surface  = serializers.FloatField()
    price    = serializers.FloatField()
    status   = serializers.CharField()
    owner_id = serializers.CharField()


class ParcelDetailSerializer(ParcelListSerializer):
    description       = serializers.CharField()
    document_hash     = serializers.CharField()
    blockchain_tx_hash = serializers.CharField()
    ipfs_hash         = serializers.CharField()
    location          = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.location:
            return {"latitude": obj.location.latitude, "longitude": obj.location.longitude}
        return None


class ValidateParcelSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    reason   = serializers.CharField(required=False, allow_blank=True)