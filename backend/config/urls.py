from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.presentation.views import AuthViewSet, UserViewSet
from apps.parcels.presentation.views import ParcelViewSet
from apps.transactions.presentation.views import TransactionViewSet

router = DefaultRouter()
router.register(r"auth",         AuthViewSet,        basename="auth")
router.register(r"utilisateurs", UserViewSet,        basename="user")
router.register(r"parcelles",    ParcelViewSet,      basename="parcel")
router.register(r"transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/health/", lambda r: __import__("django.http", fromlist=["JsonResponse"]).JsonResponse({"status": "ok"})),
]
