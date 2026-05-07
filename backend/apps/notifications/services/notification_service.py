"""
apps/notifications/services/notification_service.py
────────────────────────────────────────────────
Service de notifications — Sen_parcelle.
Centralise l'envoi d'emails, SMS et notifications push.
"""

from typing import Optional
from django.conf import settings


class NotificationService:
    """
    Service de notifications multi-canal.
    Pour l'instant, les notifications sont simulées (log uniquement).
    À brancher sur les adapters réels (Twilio, Orange SMS, Firebase, etc.).
    """

    def __init__(self, sms_adapter=None, email_adapter=None, push_adapter=None):
        self.sms_adapter = sms_adapter
        self.email_adapter = email_adapter
        self.push_adapter = push_adapter

    # ─── Notifications Parcelles ───

    def notify_parcel_submitted(self, user, parcel) -> None:
        """Notification après soumission d'une parcelle."""
        msg = f"[PARCEL SUBMITTED] Parcelle {parcel.id} soumise par {user.email}"
        print(msg)  # Remplacer par log structuré
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Votre parcelle {parcel.id} a été soumise.")

    def notify_parcel_validated(self, user, parcel) -> None:
        """Notification après validation admin."""
        msg = f"[PARCEL VALIDATED] Parcelle {parcel.id} validée"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Votre parcelle {parcel.id} a été validée !")

    def notify_parcel_rejected(self, user, parcel, reason: str) -> None:
        """Notification après rejet."""
        msg = f"[PARCEL REJECTED] Parcelle {parcel.id} rejetée: {reason}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Votre parcelle {parcel.id} a été rejetée.")

    # ─── Notifications Transactions ───

    def notify_payment_initiated(self, user, transaction) -> None:
        """Notification d'initiation de paiement."""
        msg = f"[PAYMENT INITIATED] Transaction {transaction.id} par {user.email}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Paiement de {transaction.amount} initié.")

    def notify_payment_confirmed(self, user, transaction) -> None:
        """Notification de confirmation de paiement."""
        msg = f"[PAYMENT CONFIRMED] Transaction {transaction.id} confirmée"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Paiement de {transaction.amount} confirmé !")

    def notify_payment_failed(self, user, transaction, reason: str) -> None:
        """Notification d'échec de paiement."""
        msg = f"[PAYMENT FAILED] Transaction {transaction.id}: {reason}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Échec du paiement: {reason}")

    # ─── Notifications KYC ───

    def notify_kyc_approved(self, user) -> None:
        """Notification après approbation KYC."""
        msg = f"[KYC APPROVED] Utilisateur {user.email}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, "Votre KYC a été approuvé !")

    def notify_kyc_rejected(self, user, reason: str) -> None:
        """Notification après rejet KYC."""
        msg = f"[KYC REJECTED] Utilisateur {user.email}: {reason}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Votre KYC a été rejeté: {reason}")

    # ─── Notifications Auth ───

    def notify_login_otp(self, user, otp_code: str) -> None:
        """Envoi du code OTP à l'utilisateur."""
        msg = f"[OTP SENT] Code {otp_code} envoyé à {user.email}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, f"Votre code de connexion: {otp_code}")

    def notify_suspicious_activity(self, user, activity: str) -> None:
        """Alerte sécurité."""
        msg = f"[SECURITY ALERT] {activity} sur compte {user.email}"
        print(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.phone_number, "Alerte de sécurité sur votre compte.")
