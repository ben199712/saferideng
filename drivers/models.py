from django.conf import settings
from django.db import models


class DriverProfile(models.Model):
    """A driver-specific profile for verification and registration."""

    class VerificationStatus(models.TextChoices):
        pending = "pending", "Pending"
        verified = "verified", "Verified"
        flagged = "flagged", "Flagged"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )

    # Driver identity / license
    license_number = models.CharField(max_length=64, blank=True)

    # Vehicle details
    vehicle_make = models.CharField(max_length=80, blank=True)
    vehicle_model = models.CharField(max_length=80, blank=True)
    vehicle_plate_number = models.CharField(max_length=20, blank=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.pending,
        db_index=True,
    )
    is_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DriverProfile({self.user_id})"

