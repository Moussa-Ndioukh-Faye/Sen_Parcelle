# ══════════════════════════════════════════════════════════════
# SERIALIZERS - USERS
# apps/users/presentation/serializers.py
# ══════════════════════════════════════════════════════════════

from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telephone = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=12, write_only=True)
    role = serializers.ChoiceField(choices=["acheteur", "vendeur"], default="acheteur")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    otp_code = serializers.RegexField(
        regex=r"^\d{6}$",
        max_length=6,
        required=False,
        allow_blank=True,
        error_messages={"invalid": "Le code OTP doit contenir exactement 6 chiffres."},
    )
