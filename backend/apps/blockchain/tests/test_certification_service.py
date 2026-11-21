"""Tests du service d'orchestration blockchain (IPFS + Polygon), adapters mockés."""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.blockchain.application.services.blockchain_service import BlockchainService
from core.exceptions.base import BusinessRuleViolationException

PARCEL_ID = str(uuid.uuid4())
WALLET = "0x" + "ab" * 20


def make_parcel(**overrides):
    data = {
        "id": PARCEL_ID,
        "document_hash": "ab" * 32,
        "titre": "Terrain Diamniadio",
        "region": "Dakar",
        "superficie": 300.0,
        "prix": 15_000_000,
        "owner_id": str(uuid.uuid4()),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def adapters():
    polygon = MagicMock()
    polygon.register_parcel.return_value = {
        "tx_hash": "0xtx",
        "block_number": 42,
        "gas_used": 21000,
        "contract_address": "0xcontract",
    }
    ipfs = MagicMock()
    ipfs.pin_metadata.return_value = "QmCid"
    return polygon, ipfs


@pytest.fixture
def service(adapters):
    polygon, ipfs = adapters
    svc = BlockchainService(polygon, ipfs)
    return svc


class TestCertifyParcel:
    def test_certifie_et_retourne_le_resultat(self, service, adapters):
        polygon, ipfs = adapters
        with patch.object(service, "_get_or_create_wallet", return_value=WALLET):
            result = service.certify_parcel(make_parcel(), admin_wallet=WALLET)

        assert result.tx_hash == "0xtx"
        assert result.ipfs_hash == "QmCid"
        assert result.block_number == 42
        assert result.gas_used == 21000
        metadata = ipfs.pin_metadata.call_args.args[0]
        assert metadata["titre"] == "Terrain Diamniadio"
        kwargs = polygon.register_parcel.call_args.kwargs
        assert kwargs["parcel_id"] == uuid.UUID(PARCEL_ID).int
        assert kwargs["owner_address"] == WALLET
        assert kwargs["localisation"] == "Dakar, Sénégal"
        assert len(kwargs["document_hash"]) == 32

    def test_calcule_le_hash_si_absent_et_complete_a_32_octets(self, service, adapters):
        polygon, _ = adapters
        polygon.register_parcel.return_value = {"tx_hash": "0x1", "block_number": 1}
        with (
            patch.object(service, "_get_or_create_wallet", return_value=WALLET),
            patch.object(service, "_compute_parcel_hash", return_value="abcd"),
        ):
            result = service.certify_parcel(make_parcel(document_hash=None, prix=None), WALLET)

        kwargs = polygon.register_parcel.call_args.kwargs
        assert kwargs["document_hash"] == bytes.fromhex("abcd").ljust(32, b"\x00")
        assert kwargs["prix"] == 0
        assert result.gas_used == 0
        assert result.contract_address == ""


class TestVerifyCertificate:
    def test_certificat_valide(self, service, adapters):
        polygon, _ = adapters
        polygon.verify_document.return_value = {
            "valid": True,
            "parcel_id": 7,
            "owner": WALLET,
            "registered_at": 1_700_000_000,
        }
        result = service.verify_certificate("0x" + "cd" * 32)
        assert result.is_valid is True
        assert result.parcel_id == 7
        assert result.owner_address == WALLET

    def test_certificat_introuvable(self, service, adapters):
        polygon, _ = adapters
        polygon.verify_document.return_value = {"valid": False}
        result = service.verify_certificate("cd")
        assert result.is_valid is False
        assert "introuvable" in result.message
        assert polygon.verify_document.call_args.args[0] == bytes.fromhex("cd").ljust(32, b"\x00")

    def test_erreur_de_la_blockchain(self, service, adapters):
        polygon, _ = adapters
        polygon.verify_document.side_effect = RuntimeError("RPC indisponible")
        result = service.verify_certificate("cd")
        assert result.is_valid is False
        assert "RPC indisponible" in result.message

    def test_hash_invalide(self, service):
        result = service.verify_certificate("pas-un-hash")
        assert result.is_valid is False


class TestTransferOwnership:
    def test_transfert(self, service, adapters):
        polygon, _ = adapters
        polygon.transfer_ownership.return_value = {"tx_hash": "0xtransfer"}
        with patch.object(service, "_get_or_create_wallet", return_value=WALLET):
            result = service.transfer_ownership(PARCEL_ID, "user-1", "TX-REF-1")
        assert result == {"tx_hash": "0xtransfer"}
        kwargs = polygon.transfer_ownership.call_args.kwargs
        assert kwargs["new_owner"] == WALLET
        assert len(kwargs["tx_ref"]) == 32


class TestHelpers:
    def test_hash_de_parcelle_deterministe(self, service):
        parcel = make_parcel()
        assert service._compute_parcel_hash(parcel) == service._compute_parcel_hash(parcel)
        assert len(service._compute_parcel_hash(parcel)) == 64

    def test_id_invalide(self, service):
        with pytest.raises(ValueError, match="UUID attendu"):
            service._parcel_id_to_uint("123")

    def test_str_to_bytes32(self, service):
        assert len(service._str_to_bytes32("QmCid")) == 32


@pytest.mark.django_db
class TestWallet:
    def test_utilisateur_inexistant(self, service):
        with pytest.raises(BusinessRuleViolationException):
            service._get_or_create_wallet(str(uuid.uuid4()))

    def test_utilisateur_sans_wallet(self, service, django_user_model):
        user = django_user_model.objects.create_user(
            email="sanswallet@test.sn", telephone="+221770000001", password="x", nom="Sans Wallet"
        )
        with pytest.raises(BusinessRuleViolationException):
            service._get_or_create_wallet(str(user.id))

    def test_utilisateur_avec_wallet(self, service, django_user_model):
        user = django_user_model.objects.create_user(
            email="wallet@test.sn", telephone="+221770000002", password="x", nom="Avec Wallet"
        )
        with patch("apps.users.infrastructure.models.User.objects") as objects:
            objects.get.return_value = SimpleNamespace(wallet_address=WALLET)
            assert service._get_or_create_wallet(str(user.id)) == WALLET
