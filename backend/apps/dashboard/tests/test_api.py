import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestHealthAPI:
    def test_health_returns_ok(self):
        client = APIClient()
        resp = client.get("/api/health/", secure=False)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuthAPI:
    def test_login_fails_with_wrong_credentials(self, django_user_model):
        django_user_model.objects.create_user(
            email="admin@test.sn",
            telephone="+221771234567",
            password="SecurePass123!",
            nom="Admin",
        )
        client = APIClient()
        resp = client.post(
            "/api/auth/login/",
            {
                "email": "admin@test.sn",
                "password": "wrongpass",
            },
            format="json",
            secure=False,
        )
        assert resp.status_code == 422

    def test_me_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/utilisateurs/moi/", secure=False)
        assert resp.status_code == 401

    def test_me_returns_profile(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="user@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Moussa Faye",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/utilisateurs/moi/", secure=False)
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@test.sn"

    def test_token_refresh_fails_without_token(self):
        client = APIClient()
        resp = client.post("/api/auth/token/refresh/", {}, format="json", secure=False)
        assert resp.status_code == 400

    def test_token_verify_fails_without_token(self):
        client = APIClient()
        resp = client.post("/api/auth/token/verify/", {}, format="json", secure=False)
        assert resp.status_code == 400


class TestParcelAPI:
    def test_list_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/parcelles/", secure=False)
        assert resp.status_code == 401

    def test_auth_user_can_list(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="test@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Test",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/parcelles/", secure=False)
        assert resp.status_code == 200
        assert "results" in resp.json()


class TestTransactionAPI:
    def test_list_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/transactions/", secure=False)
        assert resp.status_code == 401

    def test_list_returns_empty(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="user@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="User",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/transactions/", secure=False)
        assert resp.status_code == 200


class TestDashboardAPI:
    def test_dashboard_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/dashboard/stats/", secure=False)
        assert resp.status_code == 401

    def test_dashboard_returns_stats(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="admin@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Admin",
            role="admin",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/dashboard/stats/", secure=False)
        assert resp.status_code == 200
        data = resp.json()
        assert "parcelles" in data
        assert "utilisateurs" in data
        assert "transactions" in data
        assert "blockchain" in data


class TestBlockchainAPI:
    def test_blockchain_info_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/blockchain/info/", secure=False)
        assert resp.status_code == 401

    def test_blockchain_info_returns_fallback(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="test@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Test",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/blockchain/info/", secure=False)
        assert resp.status_code == 200
        assert resp.json()["network"] == "Unavailable"


class TestAuditAPI:
    def test_audit_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/audit/recent/", secure=False)
        assert resp.status_code == 401

    def test_audit_recent_empty(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="user@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="User",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/audit/recent/", secure=False)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_audit_security_events(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="user@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="User",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/audit/security/", secure=False)
        assert resp.status_code == 200


class TestSchemaAPI:
    def test_schema_returns_openapi(self):
        """Test rapide que le schema existe sans vérifier le contenu complet."""
        client = APIClient()
        resp = client.get("/api/schema/", HTTP_ACCEPT="application/json", secure=False)
        assert resp.status_code == 200
        assert resp.json().get("openapi", "").startswith("3.")


class TestSecurity:
    def test_rate_limit_config(self):
        from django.conf import settings

        drf = settings.REST_FRAMEWORK
        assert "DEFAULT_THROTTLE_CLASSES" in drf
        assert "DEFAULT_THROTTLE_RATES" in drf

    def test_cors_config(self):
        from django.conf import settings

        assert hasattr(settings, "CORS_ALLOWED_ORIGINS")
