"""
tests/ — Tests unitaires Sen_parcelle
--------------------------------------
Philosophie : tester le domaine SANS base de données.
Les entités et use cases sont testés avec des mocks.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def mock_otp_service():
    svc = MagicMock()
    svc.generate.return_value = "123456"
    svc.verify.return_value   = True
    return svc

@pytest.fixture
def mock_sms_service():
    return MagicMock()

@pytest.fixture
def mock_jwt_service():
    svc = MagicMock()
    svc.generate.return_value = {"access": "tok_access", "refresh": "tok_refresh"}
    return svc

@pytest.fixture
def mock_audit_service():
    return MagicMock()

@pytest.fixture
def mock_storage_service():
    svc = MagicMock()
    svc.upload.return_value = "parcels/user123/hash/document.pdf"
    return svc

@pytest.fixture
def mock_parcel_repo():
    return MagicMock()


# ══════════════════════════════════════════════════════════════
# TESTS : Value Objects
# ══════════════════════════════════════════════════════════════

class TestEmail:
    def test_email_valide(self):
        from apps.users.domain.entities import Email
        email = Email("Moussa@Email.Com")
        assert str(email) == "moussa@email.com"   # Normalisé en minuscules

    def test_email_invalide_sans_arobase(self):
        from apps.users.domain.entities import Email
        with pytest.raises(ValueError):
            Email("moussa.email.com")

    def test_email_invalide_sans_domaine(self):
        from apps.users.domain.entities import Email
        with pytest.raises(ValueError):
            Email("moussa@")


class TestPhoneNumber:
    def test_phone_valide_format_local(self):
        from apps.users.domain.entities import PhoneNumber
        phone = PhoneNumber("776543210")
        assert str(phone) == "+221776543210"

    def test_phone_valide_format_international(self):
        from apps.users.domain.entities import PhoneNumber
        phone = PhoneNumber("+221776543210")
        assert str(phone) == "+221776543210"

    def test_phone_invalide_prefixe(self):
        from apps.users.domain.entities import PhoneNumber
        with pytest.raises(ValueError):
            PhoneNumber("336543210")   # 33 = numéro fixe pas valide ici

    def test_phone_invalide_longueur(self):
        from apps.users.domain.entities import PhoneNumber
        with pytest.raises(ValueError):
            PhoneNumber("77654")


class TestDocumentHash:
    def test_hash_valide(self):
        from apps.users.domain.entities import DocumentHash
        valid_hash = "a" * 64
        h = DocumentHash(valid_hash)
        assert str(h) == valid_hash

    def test_hash_invalide_longueur(self):
        from apps.users.domain.entities import DocumentHash
        with pytest.raises(ValueError):
            DocumentHash("abc123")


# ══════════════════════════════════════════════════════════════
# TESTS : Entité User
# ══════════════════════════════════════════════════════════════

class TestUserEntity:
    def _make_user(self, role="vendeur", kyc_status="verified", is_2fa=True):
        from apps.users.domain.entities import (
            UserEntity, Email, PhoneNumber, UserRole, KYCStatus
        )
        return UserEntity(
            id="user-123",
            nom="Moussa Faye",
            email=Email("moussa@email.com"),
            telephone=PhoneNumber("776543210"),
            role=UserRole(role),
            kyc_status=KYCStatus(kyc_status),
            is_2fa_enabled=is_2fa,
        )

    def test_vendeur_kyc_verified_peut_publier(self):
        user = self._make_user(role="vendeur", kyc_status="verified")
        assert user.can_publish_parcel() is True

    def test_vendeur_kyc_pending_ne_peut_pas_publier(self):
        user = self._make_user(role="vendeur", kyc_status="pending")
        assert user.can_publish_parcel() is False

    def test_acheteur_ne_peut_pas_publier(self):
        user = self._make_user(role="acheteur", kyc_status="verified")
        assert user.can_publish_parcel() is False

    def test_acheteur_kyc_2fa_peut_acheter(self):
        user = self._make_user(role="acheteur", kyc_status="verified", is_2fa=True)
        assert user.can_buy_parcel() is True

    def test_acheteur_sans_2fa_ne_peut_pas_acheter(self):
        user = self._make_user(role="acheteur", kyc_status="verified", is_2fa=False)
        assert user.can_buy_parcel() is False

    def test_verify_kyc_retourne_nouvelle_entite(self):
        user    = self._make_user(kyc_status="pending")
        updated = user.verify_kyc()
        from apps.users.domain.entities import KYCStatus
        assert updated.kyc_status == KYCStatus.VERIFIED
        assert user.kyc_status   == KYCStatus.PENDING   # Immuabilité


# ══════════════════════════════════════════════════════════════
# TESTS : GeoPoint + Détection fraude
# ══════════════════════════════════════════════════════════════

class TestGeoPoint:
    def test_coordonnees_valides(self):
        from apps.parcels.domain.entities import GeoPoint
        p = GeoPoint(latitude=14.7645, longitude=-17.5149)
        assert p.latitude == 14.7645

    def test_latitude_invalide(self):
        from apps.parcels.domain.entities import GeoPoint
        with pytest.raises(ValueError):
            GeoPoint(latitude=95.0, longitude=-17.5)

    def test_distance_meme_point_est_zero(self):
        from apps.parcels.domain.entities import GeoPoint
        p = GeoPoint(14.7645, -17.5149)
        assert p.distance_to_meters(p) < 1

    def test_distance_almadies_plateau(self):
        """Distance between Almadies and Plateau Dakar ≈ 8.7km."""
        from apps.parcels.domain.entities import GeoPoint
        almadies = GeoPoint(14.7278, -17.5070)
        plateau  = GeoPoint(14.6820, -17.4413)
        dist = almadies.distance_to_meters(plateau)
        assert 8000 < dist < 10000   # Entre 8 et 10km


class TestParcelEntity:
    def _make_parcel(self, status="pending"):
        from apps.parcels.domain.entities import ParcelEntity, GeoPoint, ParcelStatus
        return ParcelEntity(
            id="parcel-123",
            owner_id="user-123",
            titre="Terrain Almadies",
            description="Belle vue",
            location=GeoPoint(14.7645, -17.5149),
            region="Dakar",
            surface=500,
            price=25_000_000,
            status=ParcelStatus(status),
        )

    def test_parcel_pending_peut_etre_validee(self):
        parcel = self._make_parcel("pending")
        assert parcel.can_be_validated() is True

    def test_parcel_certifiee_ne_peut_pas_etre_validee(self):
        parcel = self._make_parcel("certified")
        assert parcel.can_be_validated() is False

    def test_parcel_certifiee_peut_etre_achetee(self):
        parcel = self._make_parcel("certified")
        assert parcel.can_be_purchased() is True

    def test_detection_doublon_proche(self):
        from apps.parcels.domain.entities import GeoPoint
        parcel  = self._make_parcel()
        nearby  = GeoPoint(14.76451, -17.51491)   # À quelques mètres
        assert parcel.is_near(nearby, threshold_m=50) is True

    def test_pas_doublon_loin(self):
        from apps.parcels.domain.entities import GeoPoint
        parcel = self._make_parcel()
        far    = GeoPoint(14.80, -17.45)           # Plusieurs km
        assert parcel.is_near(far, threshold_m=50) is False


# ══════════════════════════════════════════════════════════════
# TESTS : Use Case Register
# ══════════════════════════════════════════════════════════════

class TestRegisterUseCase:
    def _make_uc(self, mock_user_repo, mock_otp_service, mock_sms_service):
        from apps.users.application.use_cases.register import RegisterUseCase
        return RegisterUseCase(mock_user_repo, mock_otp_service, mock_sms_service)

    def test_inscription_succes(self, mock_user_repo, mock_otp_service, mock_sms_service):
        from apps.users.application.use_cases.register import RegisterInput
        from apps.users.domain.entities import UserEntity, Email, PhoneNumber, UserRole, KYCStatus

        mock_user_repo.exists_by_email.return_value = False
        mock_user_repo.exists_by_phone.return_value = False
        mock_user_repo.save.return_value = UserEntity(
            id="new-user-id",
            nom="Moussa",
            email=Email("moussa@email.com"),
            telephone=PhoneNumber("776543210"),
            role=UserRole.ACHETEUR,
            kyc_status=KYCStatus.PENDING,
        )
        mock_user_repo.set_password = MagicMock()

        uc     = self._make_uc(mock_user_repo, mock_otp_service, mock_sms_service)
        result = uc.execute(RegisterInput(
            nom="Moussa", email="moussa@email.com",
            telephone="776543210", password="motdepasse123",
        ))

        assert result.user_id  == "new-user-id"
        assert result.otp_sent is True
        mock_sms_service.send.assert_called_once()

    def test_email_duplique_leve_exception(self, mock_user_repo, mock_otp_service, mock_sms_service):
        from apps.users.application.use_cases.register import RegisterInput
        from core.exceptions.base import DuplicateEntityException

        mock_user_repo.exists_by_email.return_value = True

        uc = self._make_uc(mock_user_repo, mock_otp_service, mock_sms_service)
        with pytest.raises(DuplicateEntityException):
            uc.execute(RegisterInput(
                nom="Moussa", email="moussa@email.com",
                telephone="776543210", password="motdepasse123",
            ))

    def test_mot_de_passe_trop_court(self, mock_user_repo, mock_otp_service, mock_sms_service):
        from apps.users.application.use_cases.register import RegisterInput
        from core.exceptions.base import ValidationException

        mock_user_repo.exists_by_email.return_value = False
        mock_user_repo.exists_by_phone.return_value = False

        uc = self._make_uc(mock_user_repo, mock_otp_service, mock_sms_service)
        with pytest.raises(ValidationException):
            uc.execute(RegisterInput(
                nom="Moussa", email="moussa@email.com",
                telephone="776543210", password="123",  # Trop court
            ))
