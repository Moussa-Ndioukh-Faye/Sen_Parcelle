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
        """Test de création d'un log d'audit."""
        log = AuditLog.objects.create(
            user_id='12345678-1234-5678-1234-567812345678',
            action='login_success',
            details={'ip': '127.0.0.1'},
            ip_address='127.0.0.1',
        )
        self.assertEqual(log.action, 'login_success')
        self.assertEqual(log.ip_address, '127.0.0.1')

    def test_audit_log_hash_integrity(self):
        """Test de l'intégrité du hash."""
        log1 = AuditLog.objects.create(
            user_id='12345678-1234-5678-1234-567812345678',
            action='test_action',
            details={},
        )
        log2 = AuditLog.objects.create(
            user_id='12345678-1234-5678-1234-567812345678',
            action='test_action_2',
            details={},
        )
        # Les hashs doivent être différents
        self.assertNotEqual(log1.hash, log2.hash)


class TestAuditService(TestCase):
    """Tests du service d'audit."""

    def setUp(self):
        self.audit_service = AuditService()

    def test_log_success(self):
        """Test d'enregistrement d'un événement."""
        result = self.audit_service.log(
            user_id='12345678-1234-5678-1234-567812345678',
            action='login_success',
            details={'method': 'password'},
        )
        self.assertTrue(result)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_get_user_history(self):
        """Test de récupération de l'historique."""
        user_id = '12345678-1234-5678-1234-567812345678'
        AuditLog.objects.create(user_id=user_id, action='action1', details={})
        AuditLog.objects.create(user_id=user_id, action='action2', details={})

        history = self.audit_service.get_user_history(user_id)
        self.assertEqual(len(history), 2)

    def test_get_security_events(self):
        """Test de récupération des événements de sécurité."""
        AuditLog.objects.create(
            user_id='12345678-1234-5678-1234-567812345678',
            action='login_failed',
            details={'reason': 'bad_password'},
        )
        AuditLog.objects.create(
            user_id='12345678-1234-5678-1234-567812345678',
            action='login_success',
            details={},
        )

        events = self.audit_service.get_security_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].action, 'login_failed')
