"""
apps/parcels/application/use_cases/test_submit_parcel.py
─────────────────────────────────────────────────────────
Tests pour SubmitParcelUseCase, ValidateParcelUseCase, SearchParcelsUseCase.
"""

from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.parcels.domain.entities import ParcelStatus


class TestSubmitParcelUseCase(TestCase):
    """Tests du use case de soumission de parcelle."""

    def setUp(self):
        self.mock_parcel_repo = Mock()
        self.mock_user_repo = Mock()
        self.mock_storage = Mock()
        self.mock_notif = Mock()
        self.mock_audit = Mock()

        from apps.parcels.application.use_cases.submit_parcel import SubmitParcelUseCase
        self.uc = SubmitParcelUseCase(
            parcel_repo=self.mock_parcel_repo,
            user_repo=self.mock_user_repo,
            storage_service=self.mock_storage,
            notification_service=self.mock_notif,
            audit_service=self.mock_audit,
        )

    @patch('apps.parcels.application.use_cases.submit_parcel.hashlib')
    def test_submit_parcel_success(self, mock_hashlib):
        """Test de soumission réussie."""
        from apps.parcels.application.use_cases.submit_parcel import SubmitParcelInput

        # Mock user avec KYC vérifié
        mock_user = Mock()
        mock_user.is_kyc_verified = True
        mock_user.can_publish_parcel.return_value = True
        self.mock_user_repo.get_by_id.return_value = mock_user

        # Mock hash SHA-256
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = 'abc123def456'
        mock_hashlib.sha256.return_value = mock_hash

        # Mock storage upload
        self.mock_storage.upload.return_value = 'https://example.com/doc.pdf'

        # Mock parcel crée
        mock_parcel = Mock()
        mock_parcel.id = '12345678-1234-5678-1234-567812345678'
        mock_parcel.status = ParcelStatus.PENDING
        self.mock_parcel_repo.save.return_value = mock_parcel

        # Pas de doublon géographique
        self.mock_parcel_repo.find_nearby_active.return_value = []

        input_data = SubmitParcelInput(
            owner_id='user-123',
            titre='Parcelle Test',
            description='Description test',
            localisation='Almadies, Dakar',
            region='Dakar',
            latitude=14.6928,
            longitude=-17.4467,
            superficie=500.0,
            prix=5000000,
            type_terrain='residentiel',
            document_bytes=b'fake_doc',
            document_name='doc.pdf',
        )

        _ = self.uc.execute(input_data)

        self.mock_parcel_repo.save.assert_called_once()
        self.mock_storage.upload.assert_called_once()
        self.mock_notif.notify_admins.assert_called_once()

    def test_submit_without_kyc(self):
        """Test de soumission sans KYC vérifié."""
        from apps.parcels.application.use_cases.submit_parcel import SubmitParcelInput
        from core.exceptions.base import InvalidKYCStatusException

        mock_user = Mock()
        mock_user.is_kyc_verified = False
        mock_user.can_publish_parcel.return_value = False
        self.mock_user_repo.get_by_id.return_value = mock_user

        input_data = SubmitParcelInput(
            owner_id='user-123', titre='Test', description='Test',
            localisation='Test',
            region='Dakar', latitude=14.6928, longitude=-17.4467,
            superficie=500.0, prix=5000000, type_terrain='residentiel',
            document_bytes=b'fake', document_name='doc.pdf',
        )

        with pytest.raises(InvalidKYCStatusException):
            self.uc.execute(input_data)


class TestValidateParcelUseCase(TestCase):
    """Tests du use case de validation."""

    def setUp(self):
        self.mock_parcel_repo = Mock()
        self.mock_notif = Mock()
        self.mock_audit = Mock()
        self.mock_celery = Mock()

        from apps.parcels.application.use_cases.submit_parcel import ValidateParcelUseCase
        self.uc = ValidateParcelUseCase(
            parcel_repo=self.mock_parcel_repo,
            blockchain_service=None,
            notification_service=self.mock_notif,
            audit_service=self.mock_audit,
            celery_app=self.mock_celery,
        )

    def test_validate_parcel_success(self):
        """Test de validation réussie."""
        from apps.parcels.application.use_cases.submit_parcel import ValidateParcelInput

        mock_parcel = Mock()
        mock_parcel.id = 'parcel-123'
        mock_parcel.status = ParcelStatus.PENDING
        self.mock_parcel_repo.get_by_id.return_value = mock_parcel

        data = ValidateParcelInput(
            parcel_id='parcel-123',
            admin_id='admin-123',
            decision='approve',
        )
        _ = self.uc.execute(data)

        self.mock_parcel_repo.save.assert_called_once()
        self.mock_celery.send_task.assert_called_once()

    def test_reject_parcel(self):
        """Test de rejet de parcelle."""
        from apps.parcels.application.use_cases.submit_parcel import ValidateParcelInput

        mock_parcel = Mock()
        mock_parcel.id = 'parcel-123'
        mock_parcel.status = ParcelStatus.PENDING
        self.mock_parcel_repo.get_by_id.return_value = mock_parcel

        data = ValidateParcelInput(
            parcel_id='parcel-123',
            admin_id='admin-123',
            decision='reject',
            reason='Documents incomplets',
        )
        _ = self.uc.execute(data)

        self.mock_notif.notify_user.assert_called_once()


class TestSearchParcelsUseCase(TestCase):
    """Tests du use case de recherche."""

    def setUp(self):
        self.mock_parcel_repo = Mock()
        from apps.parcels.application.use_cases.submit_parcel import SearchParcelsUseCase
        self.uc = SearchParcelsUseCase(parcel_repo=self.mock_parcel_repo)

    def test_search_by_region(self):
        """Test de recherche par région."""
        from apps.parcels.application.use_cases.submit_parcel import SearchParcelsInput

        mock_parcel1 = Mock(); mock_parcel1.prix = 100; mock_parcel1.superficie = 50
        mock_parcel2 = Mock(); mock_parcel2.prix = 200; mock_parcel2.superficie = 100
        mock_results = [mock_parcel1, mock_parcel2]
        self.mock_parcel_repo.find_by_region.return_value = mock_results

        data = SearchParcelsInput(region='Dakar')
        result = self.uc.execute(data)

        assert result.total == 2
        self.mock_parcel_repo.find_by_region.assert_called_once_with('Dakar', 'certified')
