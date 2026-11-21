"""Tests du service KYC, du nettoyage des OTP et du stockage S3."""

import hashlib
import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.users.application.services.kyc_service import KYCService, KYCSubmissionInput
from core.exceptions.base import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    ValidationException,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="kyc@test.sn", telephone="+221771111111", password="x", nom="Awa Diop"
    )


@pytest.fixture
def deps():
    return {
        "user_repo": MagicMock(),
        "storage_service": MagicMock(),
        "sms_service": MagicMock(),
        "notification_service": MagicMock(),
        "audit_service": MagicMock(),
    }


def entity(status="pending"):
    return SimpleNamespace(nom="Awa Diop", kyc_status=SimpleNamespace(value=status))


def submission(user_id, **overrides):
    data = {
        "user_id": user_id,
        "document_type": "cni",
        "document_bytes": b"contenu-cni",
        "document_name": "cni.pdf",
    }
    data.update(overrides)
    return KYCSubmissionInput(**data)


class TestSubmitKYC:
    def test_soumission_complete(self, user, deps):
        deps["user_repo"].get_by_id.return_value = entity()
        service = KYCService(**deps)

        result = service.submit_kyc(submission(str(user.id)))

        expected_hash = hashlib.sha256(b"contenu-cni").hexdigest()
        assert result.document_hash == expected_hash
        upload = deps["storage_service"].upload_private.call_args.kwargs
        assert upload["content_type"] == "application/pdf"
        assert upload["key"].startswith(f"kyc/{user.id}/cni/")
        deps["notification_service"].notify_admins.assert_called_once()
        deps["audit_service"].log.assert_called_once()
        user.refresh_from_db()
        assert user.kyc_document_hash == expected_hash
        assert user.kyc_status == "pending"

    def test_image_jpeg(self, user, deps):
        deps["user_repo"].get_by_id.return_value = entity()
        KYCService(**deps).submit_kyc(submission(str(user.id), document_name="cni.jpg"))
        assert deps["storage_service"].upload_private.call_args.kwargs["content_type"] == "image/jpeg"

    def test_type_de_document_invalide(self, deps):
        with pytest.raises(ValidationException):
            KYCService(**deps).submit_kyc(submission("u1", document_type="facture"))

    def test_fichier_trop_volumineux(self, deps):
        big = b"0" * (11 * 1024 * 1024)
        with pytest.raises(ValidationException):
            KYCService(**deps).submit_kyc(submission("u1", document_bytes=big))

    def test_utilisateur_introuvable(self, deps):
        deps["user_repo"].get_by_id.return_value = None
        with pytest.raises(EntityNotFoundException):
            KYCService(**deps).submit_kyc(submission("u1"))

    def test_deja_verifie(self, deps):
        deps["user_repo"].get_by_id.return_value = entity("verified")
        with pytest.raises(BusinessRuleViolationException):
            KYCService(**deps).submit_kyc(submission("u1"))


class TestKYCStatus:
    def test_statut(self, user, deps):
        status = KYCService(**deps).get_kyc_status(str(user.id))
        assert status["kyc_status"] == "pending"
        assert status["has_document"] is False
        assert "cours de vérification" in status["message"]

    def test_utilisateur_introuvable(self, deps):
        with pytest.raises(EntityNotFoundException):
            KYCService(**deps).get_kyc_status(str(uuid.uuid4()))

    @pytest.mark.parametrize(
        ("status", "fragment"),
        [("verified", "vérifiée"), ("rejected", "refusés"), ("autre", "inconnu")],
    )
    def test_messages(self, status, fragment):
        assert fragment in KYCService._get_status_message(status)


class TestCleanupOTP:
    def test_supprime_les_codes_anciens(self, user):
        from apps.users.infrastructure.models import OTPCode
        from apps.users.tasks import cleanup_expired_otp

        now = timezone.now()
        OTPCode.objects.create(user=user, code="111111", expires_at=now - timedelta(days=2))
        OTPCode.objects.create(user=user, code="222222", expires_at=now + timedelta(minutes=5))

        assert cleanup_expired_otp() == {"cleaned": 1}
        assert OTPCode.objects.filter(code="222222").exists()
        assert not OTPCode.objects.filter(code="111111").exists()


AWS_TEST_SETTINGS = override_settings(
    AWS_ACCESS_KEY_ID="key",
    AWS_SECRET_ACCESS_KEY="secret",
    AWS_S3_REGION_NAME="eu-west-1",
    AWS_STORAGE_BUCKET_NAME="bucket-test",
)


class TestS3Storage:
    @AWS_TEST_SETTINGS
    @patch("boto3.client")
    def test_uploads_et_url_signee(self, client_factory):
        from infrastructure.storage.s3 import S3StorageService

        client = client_factory.return_value
        client.generate_presigned_url.return_value = "https://signed"
        storage = S3StorageService()

        assert storage.upload(b"a", "photos/p.jpg", "image/jpeg") == "photos/p.jpg"
        assert storage.upload_private(b"b", "kyc/doc.pdf", "application/pdf") == "kyc/doc.pdf"
        assert storage.get_presigned_url("kyc/doc.pdf", expires_in=60) == "https://signed"

        calls = client.put_object.call_args_list
        assert all(c.kwargs["ACL"] == "private" and c.kwargs["Bucket"] == "bucket-test" for c in calls)
        assert client.generate_presigned_url.call_args.kwargs["ExpiresIn"] == 60
