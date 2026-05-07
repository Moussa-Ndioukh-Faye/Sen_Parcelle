"""
apps/blockchain/tests/test_blockchain_service.py
─────────────────────────────────────────────────────────
Tests pour BlockchainService (orchestration IPFS + Polygon).
"""

from unittest.mock import Mock, patch, MagicMock
import pytest
from django.test import TestCase


class TestBlockchainService(TestCase):
    """Tests du service blockchain."""

    def setUp(self):
        from apps.blockchain.application.services.blockchain_service import BlockchainService
        self.service = BlockchainService()

    @patch('apps.blockchain.application.services.blockchain_service.PinataAdapter')
    @patch('apps.blockchain.application.services.blockchain_service.PolygonAdapter')
    def test_certify_parcel_success(self, mock_polygon, mock_pinata):
        """Test de certification réussie d'une parcelle."""
        # Mock Pinata
        mock_pinata_instance = Mock()
        mock_pinata.return_value = mock_pinata_instance
        mock_pinata_instance.pin_json.return_value = 'QmTest123456789'

        # Mock Polygon
        mock_polygon_instance = Mock()
        mock_polygon.return_value = mock_polygon_instance
        mock_polygon_instance.register_parcel.return_value = '0xTxHash123'

        # Mock parcel data
        parcel_data = {
            'id': '12345678-1234-5678-1234-567812345678',
            'titre': 'Parcelle Test',
            'owner_id': '87654321-4321-8765-4321-876543210987',
            'surface': 500.0,
            'prix': 5000000,
            'region': 'Dakar',
            'latitude': 14.6928,
            'longitude': -17.4467,
            'document_hash': 'abc123def456',
        }

        result = self.service.certify_parcel(parcel_data)

        self.assertIsNotNone(result)
        self.assertIn('tx_hash', result)
        self.assertIn('ipfs_cid', result)

    def test_certify_parcel_missing_data(self):
        """Test avec des données manquantes."""
        parcel_data = {'id': 'test-id'}  # Données incomplètes

        with self.assertRaises(ValueError):
            self.service.certify_parcel(parcel_data)

    @patch('apps.blockchain.application.services.blockchain_service.PolygonAdapter')
    def test_transfer_ownership(self, mock_polygon):
        """Test de transfert de propriété."""
        mock_polygon_instance = Mock()
        mock_polygon.return_value = mock_polygon_instance
        mock_polygon_instance.transfer_ownership.return_value = '0xTransferHash'

        result = self.service.transfer_ownership(
            parcel_id='12345678-1234-5678-1234-567812345678',
            new_owner_id='87654321-4321-8765-4321-876543210987',
            tx_hash='0xPaymentTx'
        )

        self.assertEqual(result, '0xTransferHash')
