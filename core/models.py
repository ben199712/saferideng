from django.conf import settings
from django.db import models


class EmailNotificationLog(models.Model):
    class Status(models.TextChoices):
        pending = "pending", "Pending"
        sent = "sent", "Sent"
        failed = "failed", "Failed"
        skipped = "skipped", "Skipped"

    event_type = models.CharField(max_length=64, db_index=True)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_notification_actor_logs",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_notification_target_logs",
    )
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.pending, db_index=True)
    provider = models.CharField(max_length=40, default="resend")
    provider_message_id = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["to_email", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type}:{self.to_email}:{self.status}"
