# ════════════════════════════════════════════════════════════════
# SERIALIZERS TRANSACTIONS
# apps/transactions/presentation/serializers.py
# ════════════════════════════════════════════════════════════════

from rest_framework import serializers

class InitiatePaymentSerializer(serializers.Serializer):
    parcel_id = serializers.UUIDField()
    provider  = serializers.ChoiceField(choices=["wave", "orange_money"])

class TransactionSerializer(serializers.Serializer):
    id             = serializers.UUIDField()
    parcel_id      = serializers.UUIDField()
    buyer_id       = serializers.UUIDField()
    amount_fcfa    = serializers.FloatField()
    provider       = serializers.CharField()
    status         = serializers.CharField()
    payment_ref    = serializers.CharField(required=False, allow_null=True)
    blockchain_tx  = serializers.CharField(required=False, allow_null=True)
    created_at     = serializers.DateTimeField()
