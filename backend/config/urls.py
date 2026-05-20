from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.blockchain.presentation.views import AuditViewSet, BlockchainViewSet, NotificationViewSet
from apps.dashboard.presentation.views import DashboardViewSet
from apps.parcels.presentation.views import ParcelViewSet
from apps.transactions.presentation.views import TransactionViewSet
from apps.users.presentation.views import AuthViewSet, UserViewSet

router = DefaultRouter()
router.register(r"auth",             AuthViewSet,        basename="auth")
router.register(r"utilisateurs",     UserViewSet,        basename="user")
router.register(r"parcelles",        ParcelViewSet,      basename="parcel")
router.register(r"transactions",     TransactionViewSet, basename="transaction")
router.register(r"blockchain",       BlockchainViewSet,  basename="blockchain")
router.register(r"audit",            AuditViewSet,       basename="audit")
router.register(r"notifications",    NotificationViewSet, basename="notification")
router.register(r"dashboard",        DashboardViewSet,   basename="dashboard")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/health/", lambda r: __import__("django.http", fromlist=["JsonResponse"]).JsonResponse({"status": "ok"})),

    # Documentation API (Swagger/OpenAPI)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
