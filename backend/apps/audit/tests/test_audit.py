"""
apps/audit/tests/test_audit.py
─────────────────────────────────────────────────────────
Tests pour AuditService et AuditLog.
"""

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.audit.services import AuditService


class TestAuditLog(TestCase):
    """Tests du modèle AuditLog."""

    def test_create_audit_log(self):
        """Test de creation d'un log d'audit."""
        log = AuditLog.objects.create(
            user_id="12345678-1234-5678-1234-567812345678",
            action="login_success",
            metadata={"ip": "127.0.0.1"},
            ip_address="127.0.0.1",
        )
        assert log.action == "login_success"
        assert log.ip_address == "127.0.0.1"

    def test_audit_log_hash_integrity(self):
        """Test de l'intégrité du hash."""
        log1 = AuditLog.objects.create(
            user_id="12345678-1234-5678-1234-567812345678",
            action="test_action",
            metadata={},
        )
        log2 = AuditLog.objects.create(
            user_id="12345678-1234-5678-1234-567812345678",
            action="test_action_2",
            metadata={},
        )
        # Les hashs doivent être différents
        assert log1.integrity_hash != log2.integrity_hash


class TestAuditService(TestCase):
    """Tests du service d'audit."""

    def setUp(self):
        self.audit_service = AuditService()

    def test_log_success(self):
        """Test d'enregistrement d'un événement."""
        self.audit_service.log(
            user_id="12345678-1234-5678-1234-567812345678",
            action="login_success",
            metadata={"method": "password"},
        )
        assert AuditLog.objects.count() == 1

    def test_get_user_history(self):
        """Test de récupération de l'historique."""
        user_id = "12345678-1234-5678-1234-567812345678"
        AuditLog.objects.create(user_id=user_id, action="action1", metadata={})
        AuditLog.objects.create(user_id=user_id, action="action2", metadata={})

        history = self.audit_service.get_user_history(user_id)
        assert len(history) == 2

    def test_get_security_events(self):
        """Test de récupération des événements de sécurité."""
        AuditLog.objects.create(
            user_id="12345678-1234-5678-1234-567812345678",
            action="login_failed",
            metadata={"reason": "bad_password"},
        )
        AuditLog.objects.create(
            user_id="12345678-1234-5678-1234-567812345678",
            action="login_success",
            metadata={},
        )

        events = self.audit_service.get_security_events()
        assert len(events) == 1
        assert events[0]["action"] == "login_failed"
