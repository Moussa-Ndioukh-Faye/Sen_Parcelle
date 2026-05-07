# ══════════════════════════════════════════════════════════════
# SERVICE AUDIT
# ══════════════════════════════════════════════════════════════

class AuditService:
    """
    Service d'audit centralisé.
    Utilisé par tous les use cases et services.
    """

    def log(self, user_id: str, action: str, metadata: dict,
            ip_address: str = None, user_agent: str = None):
        """
        Enregistre une action dans le journal d'audit.
        Non bloquant : les erreurs d'audit ne doivent pas affecter le flux principal.
        """
        try:
            AuditLog.objects.create(
                user_id=user_id if user_id else None,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent or "",
                metadata=metadata,
            )
        except Exception as e:
            # Log uniquement dans les fichiers — ne pas propager
            logger.error(f"Erreur audit : action={action} user={user_id} error={e}")

    def get_user_history(self, user_id: str, limit: int = 50) -> list:
        """Retourne l'historique des actions d'un utilisateur."""
        logs = AuditLog.objects.filter(user_id=user_id)[:limit]
        return [
            {
                "action":     log.action,
                "created_at": log.created_at.isoformat(),
                "metadata":   log.metadata,
                "ip":         log.ip_address,
            }
            for log in logs
        ]

    def get_security_events(self, hours: int = 24) -> list:
        """
        Retourne les événements de sécurité récents.
        Utilisé par le dashboard admin.
        """
        from datetime import timedelta
        since = timezone.now() - timedelta(hours=hours)
        security_actions = [
            "login_failed", "account_locked",
            "password_changed", "2fa_disabled"
        ]
        return list(
            AuditLog.objects.filter(
                action__in=security_actions,
                created_at__gte=since,
            ).values("user_id", "action", "ip_address", "created_at", "metadata")
        )