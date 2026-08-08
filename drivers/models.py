from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import COUNTRY_CHOICES, GENDER_CHOICES, STATE_CHOICES, TRANSPORT_UNION_CHOICES
from .documents import DOCUMENT_REQUIREMENTS, PRIVATE_DRIVER_STORAGE, delete_backup_copy, driver_document_upload_to, format_file_size
from .fields import EncryptedCharField, EncryptedTextField
from .validators import (
    validate_driver_age,
    validate_driver_email,
    validate_driver_license_number,
    validate_e164_phone_number,
    validate_nin,
    validate_residential_address,
    validate_state_lga_pair,
    validate_union_membership_number,
)


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

    date_of_birth = models.DateField(null=True, blank=True, validators=[validate_driver_age])
    gender = models.CharField(max_length=24, choices=GENDER_CHOICES, blank=True)
    phone_number = EncryptedCharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        validators=[validate_e164_phone_number],
    )
    alternative_phone_number = EncryptedCharField(
        max_length=255,
        null=True,
        blank=True,
        validators=[validate_e164_phone_number],
    )
    email = models.EmailField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        validators=[validate_driver_email],
    )
    residential_address = EncryptedTextField(
        null=True,
        blank=True,
        validators=[validate_residential_address],
    )
    lga = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, choices=STATE_CHOICES, blank=True, db_index=True)
    nationality = models.CharField(max_length=80, choices=COUNTRY_CHOICES, blank=True)
    nin = EncryptedCharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        validators=[validate_nin],
    )
    license_number = EncryptedCharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        validators=[validate_driver_license_number],
    )
    driver_license_expiry_date = models.DateField(null=True, blank=True, db_index=True)
    transport_union = models.CharField(max_length=32, choices=TRANSPORT_UNION_CHOICES, blank=True, db_index=True)
    union_membership_number = models.CharField(
        max_length=40,
        blank=True,
        validators=[validate_union_membership_number],
    )
    years_of_driving_experience = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(2), MaxValueValidator(70)],
    )

    # Legacy vehicle details still shown on the profile/dashboard until the vehicle app becomes the sole source of truth.
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

    class Meta:
        indexes = [
            models.Index(fields=["verification_status"]),
            models.Index(fields=["state"]),
            models.Index(fields=["driver_license_expiry_date"]),
        ]

    def __str__(self):
        return f"DriverProfile({self.user_id})"

    def clean(self):
        validate_state_lga_pair(self.state, self.lga)

        if self.driver_license_expiry_date and self.driver_license_expiry_date <= timezone.now().date():
            raise ValidationError({"driver_license_expiry_date": "Driver license expiry date must be in the future."})

        if self.phone_number and self.alternative_phone_number and self.phone_number == self.alternative_phone_number:
            raise ValidationError({"alternative_phone_number": "Alternative phone number must be different from the primary phone number."})

        if self.years_of_driving_experience is not None and self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            max_possible_experience = max(age - 18, 0)
            if self.years_of_driving_experience > max_possible_experience:
                raise ValidationError(
                    {
                        "years_of_driving_experience": "Driving experience cannot exceed the years reasonably possible from the driver's age."
                    }
                )

    @property
    def is_license_expiring_soon(self):
        if not self.driver_license_expiry_date:
            return False
        return self.driver_license_expiry_date <= timezone.now().date() + timezone.timedelta(days=90)

    @property
    def email_verified(self):
        return bool(self.email and self.user.email == self.email and self.user.is_verified)


class DriverDocument(models.Model):
    class PreviewKind(models.TextChoices):
        image = "image", "Image"
        pdf = "pdf", "PDF"
        generic = "generic", "Generic"

    class ScanStatus(models.TextChoices):
        pending = "pending", "Pending"
        clean = "clean", "Clean"
        skipped = "skipped", "Skipped"
        failed = "failed", "Failed"

    class DocumentType(models.TextChoices):
        passport_photograph = "passport_photograph", DOCUMENT_REQUIREMENTS["passport_photograph"]["label"]
        driver_license = "driver_license", DOCUMENT_REQUIREMENTS["driver_license"]["label"]
        nin_slip = "nin_slip", DOCUMENT_REQUIREMENTS["nin_slip"]["label"]
        proof_of_address = "proof_of_address", DOCUMENT_REQUIREMENTS["proof_of_address"]["label"]
        vehicle_registration = "vehicle_registration", DOCUMENT_REQUIREMENTS["vehicle_registration"]["label"]
        union_membership_card = "union_membership_card", DOCUMENT_REQUIREMENTS["union_membership_card"]["label"]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_documents",
    )
    document_type = models.CharField(max_length=40, choices=DocumentType.choices)
    file = models.FileField(storage=PRIVATE_DRIVER_STORAGE, upload_to=driver_document_upload_to)
    original_file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=120, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    preview_kind = models.CharField(max_length=20, choices=PreviewKind.choices, default=PreviewKind.generic)
    backup_file_name = models.CharField(max_length=255, blank=True)
    malware_scan_status = models.CharField(max_length=20, choices=ScanStatus.choices, default=ScanStatus.pending)
    malware_scan_message = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "document_type"], name="unique_driver_document_type_per_user"),
        ]
        indexes = [
            models.Index(fields=["user", "document_type"]),
            models.Index(fields=["uploaded_at"]),
        ]
        ordering = ["document_type"]

    def __str__(self):
        return f"{self.user_id}:{self.document_type}"

    @property
    def is_required(self):
        return DOCUMENT_REQUIREMENTS[self.document_type]["required"]

    @property
    def document_label(self):
        return DOCUMENT_REQUIREMENTS[self.document_type]["label"]

    @property
    def preview_available(self):
        return self.preview_kind in {self.PreviewKind.image, self.PreviewKind.pdf}

    @property
    def formatted_size(self):
        return format_file_size(self.file_size)

    def get_file_url(self):
        from django.urls import reverse

        return reverse("driver_document_file", kwargs={"pk": self.pk})

    def delete(self, using=None, keep_parents=False):
        file_name = self.file.name
        backup_name = self.backup_file_name
        storage = self.file.storage
        response = super().delete(using=using, keep_parents=keep_parents)
        if file_name and storage.exists(file_name):
            storage.delete(file_name)
        delete_backup_copy(backup_name)
        return response
