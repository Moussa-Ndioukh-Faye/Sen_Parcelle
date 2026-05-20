# ══════════════════════════════════════════════════════════════
# STORAGE S3
# infrastructure/storage/s3.py
# ══════════════════════════════════════════════════════════════

class S3StorageService:
    """Service de stockage AWS S3 pour documents et photos."""

    def __init__(self):
        import boto3
        from django.conf import settings
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self._bucket = settings.AWS_STORAGE_BUCKET_NAME

    def upload(self, content: bytes, filename: str, content_type: str) -> str:
        """Upload privé par défaut, accès via URL signée."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=filename,
            Body=content,
            ContentType=content_type,
            ACL="private",
            ServerSideEncryption="AES256",
        )
        return filename

    def upload_private(self, content: bytes, key: str, content_type: str) -> str:
        """Upload privé (documents KYC — jamais public)."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            ACL="private",
            ServerSideEncryption="AES256",   # Chiffrement côté serveur
        )
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """URL signée temporaire pour accès sécurisé aux documents privés."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
