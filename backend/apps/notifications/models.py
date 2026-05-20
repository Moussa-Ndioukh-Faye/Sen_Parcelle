import uuid

from django.conf import settings
from django.db import models


class NotificationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications", null=True, blank=True,
    )
    event = models.CharField(max_length=50)
    channel = models.CharField(max_length=10, choices=[
        ("sms", "SMS"), ("email", "Email"), ("push", "Push"),
    ])
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["event"]),
        ]
