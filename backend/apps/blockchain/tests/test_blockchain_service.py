import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

pytestmark = pytest.mark.django_db

# Un UUID valide (hexadécimal avec tirets) pour le test
VALID_UUID = str(uuid.uuid4())
VALID_HEX_ID = VALID_UUID.replace("-", "")

BLOCKCHAIN_SETTINGS = override_settings(
    POLYGON_RPC_URL="http://localhost:8545",
    POLYGON_PRIVATE_KEY="0x" + "ab" * 32,
    POLYGON_CONTRACT_ADDRESS="0x" + "12" * 20,
    POLYGON_ACCOUNT_ADDRESS="0x" + "12" * 20,
)


class TestPolygonAdapter:
    """Tests unitaires du PolygonAdapter avec Web3 mocké."""

    @BLOCKCHAIN_SETTINGS
    @patch("web3.Web3")
    def test_register_parcel(self, mock_web3):
        from apps.blockchain.infrastructure.adapters.polygon_adapter import (
            PolygonAdapter,
        )

        w3 = MagicMock()
        w3.eth.chain_id = 80001
        w3.eth.get_transaction_count.return_value = 1
        w3.eth.gas_price = 20000000000
        w3.to_bytes.return_value = b"\x12\x34\x56\x78"

        contract = MagicMock()
        register_fn = MagicMock()
        register_fn.build_transaction.return_value = {
            "from": "0xadmin", "nonce": 1, "gas": 400000, "gasPrice": 20000000000,
        }
        contract.functions.registerParcel.return_value = register_fn
        w3.eth.contract.return_value = contract

        signed = MagicMock()
        signed.rawTransaction = b"\x00" * 32
        w3.eth.account.sign_transaction.return_value = signed
        w3.eth.send_raw_transaction.return_value = b"\xde\xad\xbe\xef"
        receipt = MagicMock(blockNumber=42001, gasUsed=180000)
        w3.eth.wait_for_transaction_receipt.return_value = receipt
        mock_web3.HTTPProvider.return_value = "http://mock"
        mock_web3.return_value = w3

        with patch.object(PolygonAdapter, "_load_abi", return_value=[]):
            adapter = PolygonAdapter()
            result = adapter.register_parcel(
                parcel_id=VALID_UUID,
                document_hash="0xabcd",
                ipfs_hash="QmTest123",
                owner_address="0xowner",
                localisation="Dakar - Test",
                superficie=500,
                prix=25000000,
            )
            assert result["tx_hash"] == "deadbeef"
            assert result["block_number"] == 42001
            assert result["gas_used"] == 180000

    @BLOCKCHAIN_SETTINGS
    @patch("web3.Web3")
    def test_transfer_ownership(self, mock_web3):
        from apps.blockchain.infrastructure.adapters.polygon_adapter import (
            PolygonAdapter,
        )

        w3 = MagicMock()
        w3.eth.get_transaction_count.return_value = 2
        w3.eth.gas_price = 20000000000
        w3.to_bytes.return_value = b"\x12\x34\x56\x78"

        contract = MagicMock()
        transfer_fn = MagicMock()
        transfer_fn.build_transaction.return_value = {
            "from": "0xadmin", "nonce": 2, "gas": 250000, "gasPrice": 20000000000,
        }
        contract.functions.transferOwnership.return_value = transfer_fn
        w3.eth.contract.return_value = contract

        signed = MagicMock()
        signed.rawTransaction = b"\x00" * 32
        w3.eth.account.sign_transaction.return_value = signed
        w3.eth.send_raw_transaction.return_value = b"\xca\xfe\xba\xbe"
        receipt = MagicMock(blockNumber=42002, gasUsed=120000)
        w3.eth.wait_for_transaction_receipt.return_value = receipt
        mock_web3.HTTPProvider.return_value = "http://mock"
        mock_web3.return_value = w3

        with patch.object(PolygonAdapter, "_load_abi", return_value=[]):
            adapter = PolygonAdapter()
            result = adapter.transfer_ownership(
                parcel_id=VALID_UUID,
                new_owner="0xnewOwner",
                tx_ref="tx-abc-123",
            )
            assert result["tx_hash"] == "cafebabe"
            assert result["block_number"] == 42002

    @BLOCKCHAIN_SETTINGS
    @patch("web3.Web3")
    def test_verify_certificate_valid(self, mock_web3):
        from apps.blockchain.infrastructure.adapters.polygon_adapter import (
            PolygonAdapter,
        )

        w3 = MagicMock()
        contract = MagicMock()
        contract.functions.verifyDocument.return_value.call.return_value = (
            True, 1, "0xowner", 1700000000,
        )
        w3.eth.contract.return_value = contract
        w3.to_bytes.return_value = b"\x00" * 32
        mock_web3.HTTPProvider.return_value = "http://mock"
        mock_web3.return_value = w3

        with patch.object(PolygonAdapter, "_load_abi", return_value=[]):
            adapter = PolygonAdapter()
            result = adapter.verify_certificate("0xabcd")
            assert result["valide"] is True
            assert result["parcel_id"] == "0x1"

    @BLOCKCHAIN_SETTINGS
    @patch("web3.Web3")
    def test_verify_certificate_invalid(self, mock_web3):
        from apps.blockchain.infrastructure.adapters.polygon_adapter import (
            PolygonAdapter,
        )

        w3 = MagicMock()
        contract = MagicMock()
        contract.functions.verifyDocument.return_value.call.return_value = (
            False, 0, "0x0000", 0,
        )
        w3.eth.contract.return_value = contract
        w3.to_bytes.return_value = b"\x00" * 32
        mock_web3.HTTPProvider.return_value = "http://mock"
        mock_web3.return_value = w3

        with patch.object(PolygonAdapter, "_load_abi", return_value=[]):
            adapter = PolygonAdapter()
            result = adapter.verify_certificate("0xinvalid")
            assert result["valide"] is False


class TestBlockchainTasks:
    """Tests des tâches Celery blockchain avec dépendances mockées."""

    @BLOCKCHAIN_SETTINGS
    @patch("apps.blockchain.infrastructure.adapters.polygon_adapter.PolygonAdapter")
    @patch("apps.blockchain.infrastructure.adapters.ipfs_adapter.IPFSAdapter")
    @patch("apps.parcels.infrastructure.models.DjangoParcelRepository")
    def test_certify_parcel_task(
        self, MockRepo, MockIPFSAdapter, MockPolygonAdapter, django_user_model
    ):
        from apps.blockchain.tasks import certify_parcel_on_blockchain

        admin = django_user_model.objects.create_user(
            email="admin@test.sn",
            telephone="+221771234567",
            password="test123",
            nom="Admin Test",
        )

        mock_parcel = MagicMock()
        mock_parcel.id = VALID_UUID
        mock_parcel.document_hash = "0xabcd"
        mock_parcel.titre = "Terrain Test"
        mock_parcel.region = "Dakar"
        mock_parcel.superficie = 500
        mock_parcel.prix = 25000000
        mock_parcel.owner_id = str(admin.id)
        mock_parcel.blockchain_tx_hash = None
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_parcel
        MockRepo.return_value = mock_repo

        mock_ipfs = MagicMock()
        mock_ipfs.pin_metadata.return_value = "QmIPFSTest123"
        MockIPFSAdapter.return_value = mock_ipfs

        mock_adapter = MagicMock()
        mock_adapter.register_parcel.return_value = {
            "tx_hash": "0xdeadbeef",
            "block_number": 42001,
        }
        mock_adapter.get_owner_address.return_value = "0xowner"
        MockPolygonAdapter.return_value = mock_adapter

        result = certify_parcel_on_blockchain(
            parcel_id=VALID_UUID,
            admin_id=str(admin.id),
        )
        assert result["success"] is True
        assert result["tx_hash"] == "0xdeadbeef"
        mock_adapter.register_parcel.assert_called_once()

    @BLOCKCHAIN_SETTINGS
    @patch("apps.blockchain.infrastructure.adapters.polygon_adapter.PolygonAdapter")
    def test_transfer_ownership_task_structure(self, MockPolygonAdapter):
        """Vérifie que la tâche est bien définie et structurée."""
        from apps.blockchain.tasks import transfer_ownership_on_blockchain

        mock_adapter = MagicMock()
        mock_adapter.get_owner_address.return_value = "0xbuyerAddress"
        MockPolygonAdapter.return_value = mock_adapter

        assert callable(transfer_ownership_on_blockchain)
        assert transfer_ownership_on_blockchain.__name__ == "transfer_ownership_on_blockchain"
