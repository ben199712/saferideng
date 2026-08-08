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
    details_snapshot = models.JSONField(default=dict, blank=True)
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


class SOSAuthorityContact(models.Model):
    authority_name = models.CharField(max_length=160)
    official_email = models.EmailField()
    sms_phone_number = models.CharField(max_length=30)
    physical_jurisdiction = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["authority_name"]
        indexes = [
            models.Index(fields=["is_active", "authority_name"]),
            models.Index(fields=["physical_jurisdiction"]),
        ]

    def __str__(self):
        return self.authority_name


class SOSAlertDeliveryLog(models.Model):
    class RecipientType(models.TextChoices):
        authority = "authority", "Authority"
        admin = "admin", "Admin"

    class Channel(models.TextChoices):
        email = "email", "Email"
        sms = "sms", "SMS"

    class DeliveryStatus(models.TextChoices):
        pending = "pending", "Pending"
        sent = "sent", "Sent"
        failed = "failed", "Failed"
        skipped = "skipped", "Skipped"

    alert = models.ForeignKey(
        EmergencyAlert,
        on_delete=models.CASCADE,
        related_name="delivery_logs",
    )
    authority_contact = models.ForeignKey(
        "emergency.SOSAuthorityContact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_logs",
    )
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sos_delivery_logs",
    )
    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    destination = models.CharField(max_length=160)
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.pending,
        db_index=True,
    )
    provider_reference = models.CharField(max_length=160, blank=True)
    response_message = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["alert", "status"]),
            models.Index(fields=["recipient_type", "channel"]),
        ]

    def __str__(self):
        return f"{self.alert_id}:{self.recipient_type}:{self.channel}:{self.destination}"


class SOSAuthorityAccessLog(models.Model):
    class Actions(models.TextChoices):
        list = "list", "List"
        create = "create", "Create"
        update = "update", "Update"
        delete = "delete", "Delete"

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sos_authority_access_logs",
    )
    authority_contact = models.ForeignKey(
        "emergency.SOSAuthorityContact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
    )
    action = models.CharField(max_length=20, choices=Actions.choices)
    request_path = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["admin_user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        return f"{self.admin_user_id}:{self.action}:{self.created_at}"
