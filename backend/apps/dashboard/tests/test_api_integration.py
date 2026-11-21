import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestNotificationsAPI:
    def test_notifications_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/notifications/preferences/", secure=False)
        assert resp.status_code == 401

    def test_notifications_preferences(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="user@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="User",
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get("/api/notifications/preferences/", secure=False)
        assert resp.status_code == 200
        data = resp.json()
        assert "sms" in data
        assert "email" in data
        assert "push" in data


class TestSwaggerUI:
    def test_swagger_ui_accessible(self):
        """Vérifie que l'UI Swagger répond (peut rediriger vers le schema)."""
        client = APIClient()
        resp = client.get("/api/docs/", secure=False)
        # Peut retourner 200 ou 302 selon la config
        assert resp.status_code in (200, 302)

    def test_redoc_ui_accessible(self):
        client = APIClient()
        resp = client.get("/api/redoc/", secure=False)
        assert resp.status_code in (200, 302)


class TestSecurityHeaders:
    @pytest.fixture(autouse=True)
    def _auth(self, django_user_model):
        self.user = django_user_model.objects.create_user(
            email="admin@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Admin",
        )

    def test_security_middleware_active(self):
        from django.conf import settings

        middleware = settings.MIDDLEWARE
        names = [m.split(".")[-1] for m in middleware]
        assert "SecurityMiddleware" in names or "SecurityHeadersMiddleware" in names

    def test_cors_middleware_active(self):
        from django.conf import settings

        middleware = settings.MIDDLEWARE
        names = [m.split(".")[-1] for m in middleware]
        assert "CorsMiddleware" in names or "CorsMiddleware" in str(middleware)
