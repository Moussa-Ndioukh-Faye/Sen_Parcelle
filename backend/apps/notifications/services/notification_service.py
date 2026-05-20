"""
apps/notifications/services/notification_service.py
────────────────────────────────────────────────
Service de notifications — Sen_parcelle.
Centralise l'envoi d'emails, SMS et notifications push.
"""

import logging

logger = logging.getLogger(__name__)


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
        logger.info(msg)  # Remplacer par log structuré
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Votre parcelle {parcel.id} a été soumise.")

    def notify_parcel_validated(self, user, parcel) -> None:
        """Notification après validation admin."""
        msg = f"[PARCEL VALIDATED] Parcelle {parcel.id} validée"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Votre parcelle {parcel.id} a été validée !")

    def notify_parcel_rejected(self, user, parcel, reason: str) -> None:
        """Notification après rejet."""
        msg = f"[PARCEL REJECTED] Parcelle {parcel.id} rejetée: {reason}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Votre parcelle {parcel.id} a été rejetée.")

    # ─── Notifications Transactions ───

    def notify_payment_initiated(self, user, transaction) -> None:
        """Notification d'initiation de paiement."""
        msg = f"[PAYMENT INITIATED] Transaction {transaction.id} par {user.email}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Paiement de {transaction.amount_fcfa} initié.")

    def notify_payment_confirmed(self, user, transaction) -> None:
        """Notification de confirmation de paiement."""
        msg = f"[PAYMENT CONFIRMED] Transaction {transaction.id} confirmée"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Paiement de {transaction.amount_fcfa} confirmé !")

    def notify_payment_failed(self, user, transaction, reason: str) -> None:
        """Notification d'échec de paiement."""
        msg = f"[PAYMENT FAILED] Transaction {transaction.id}: {reason}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Échec du paiement: {reason}")

    # ─── Notifications KYC ───

    def notify_kyc_approved(self, user) -> None:
        """Notification après approbation KYC."""
        msg = f"[KYC APPROVED] Utilisateur {user.email}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, "Votre KYC a été approuvé !")

    def notify_kyc_rejected(self, user, reason: str) -> None:
        """Notification après rejet KYC."""
        msg = f"[KYC REJECTED] Utilisateur {user.email}: {reason}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Votre KYC a été rejeté: {reason}")

    # ─── Notifications Auth ───

    def notify_login_otp(self, user, otp_code: str) -> None:
        """Envoi du code OTP à l'utilisateur."""
        msg = f"[OTP SENT] Code {otp_code} envoyé à {user.email}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, f"Votre code de connexion: {otp_code}")

    def notify_suspicious_activity(self, user, activity: str) -> None:
        """Alerte sécurité."""
        msg = f"[SECURITY ALERT] {activity} sur compte {user.email}"
        logger.info(msg)
        if self.sms_adapter:
            self.sms_adapter.send(user.telephone, "Alerte de sécurité sur votre compte.")

    # ─── Méthodes Génériques ───

    def notify_user(self, user_id: str, event: str, data: dict) -> None:
        """
        Méthode générique pour notifier un utilisateur.
        Délègue aux méthodes spécifiques selon l'événement.
        """
        from apps.notifications.models import NotificationLog
        from apps.users.infrastructure.models import User
        try:
            user = User.objects.get(id=user_id)

            # Log en base de données
            NotificationLog.objects.create(
                user=user,
                event=event,
                channel="sms", # Par défaut pour le moment
                message=str(data.get("message", f"Nouvel événement: {event}")),
                metadata=data
            )

            msg = f"[NOTIFICATION USER] Event={event} User={user.email} Data={data}"
            logger.info(msg)

            # Envoi SMS réel si adapter présent
            if self.sms_adapter and hasattr(user, 'telephone'):
                self.sms_adapter.send(user.telephone, str(data.get("message", event)))

        except User.DoesNotExist:
            logger.warning(f"Erreur notification : utilisateur {user_id} introuvable.")

    def notify_admins(self, event: str, data: dict) -> None:
        """
        Méthode générique pour notifier les administrateurs.
        """
        msg = f"[NOTIFICATION ADMIN] Event={event} Data={data}"
        logger.info(msg)
        # Implémentation réelle : envoi email/slack aux admins
