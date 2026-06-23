import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class EmergencyContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=30)
    relationship = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.relationship})"


class EmergencyAlert(models.Model):
    class AlertTypes(models.TextChoices):
        sos = "sos", "SOS"
        panic = "panic", "Panic"
        suspicious_activity = "suspicious_activity", "Suspicious Activity"

    class AlertStatus(models.TextChoices):
        active = "active", "Active"
        resolved = "resolved", "Resolved"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    alert_type = models.CharField(
        max_length=30,
        choices=AlertTypes.choices,
        db_index=True,
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emergency_alerts",
    )
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.active,
        db_index=True,
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["alert_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["trip", "status"]),
        ]

    def __str__(self):
        return f"Alert {self.uuid} - {self.trip}"

    def resolve(self):
        self.status = self.AlertStatus.resolved
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at"])
