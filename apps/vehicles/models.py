import uuid
from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
    class VehicleTypes(models.TextChoices):
        taxi = "taxi", "Taxi"
        bus = "bus", "Bus"
        keke = "keke", "Keke"
        shuttle = "shuttle", "Shuttle"

    class VerificationStatus(models.TextChoices):
        pending = "pending", "Pending"
        approved = "approved", "Approved"
        rejected = "rejected", "Rejected"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    plate_number = models.CharField(max_length=20, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleTypes.choices)
    vehicle_make = models.CharField(max_length=80)
    vehicle_model = models.CharField(max_length=80)
    vehicle_color = models.CharField(max_length=40)
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(date.today().year + 1)]
    )
    registered_route = models.CharField(max_length=120)
    insurance_number = models.CharField(max_length=80)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.pending,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["plate_number"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self):
        return f"{self.plate_number} - {self.driver.full_name}"

    def approve(self):
        self.verification_status = self.VerificationStatus.approved
        self.is_active = True
        self.approved_at = timezone.now()
        self.save(update_fields=["verification_status", "is_active", "approved_at", "updated_at"])

    def reject(self):
        self.verification_status = self.VerificationStatus.rejected
        self.is_active = False
        self.approved_at = None
        self.save(update_fields=["verification_status", "is_active", "approved_at", "updated_at"])

    def mark_pending(self):
        self.verification_status = self.VerificationStatus.pending
        self.is_active = True
        self.approved_at = None
        self.save(update_fields=["verification_status", "is_active", "approved_at", "updated_at"])

    @property
    def approval_date(self):
        return self.approved_at

    @property
    def is_verified(self):
        return (
            self.verification_status == self.VerificationStatus.approved
            and self.is_active
        )

    @property
    def is_rejected(self):
        return self.verification_status == self.VerificationStatus.rejected

    @property
    def is_suspended(self):
        return not self.is_active


class VehicleQRCode(models.Model):
    vehicle = models.OneToOneField(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="qr_code",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    qr_image = models.ImageField(upload_to="vehicle_qrcodes/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
        ]

    def __str__(self):
        return f"QRCode({self.vehicle.plate_number})"


class QRScanLog(models.Model):
    qr_code = models.ForeignKey(
        VehicleQRCode,
        on_delete=models.CASCADE,
        related_name="scan_logs",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"Scan({self.qr_code.vehicle.plate_number} at {self.scanned_at})"


