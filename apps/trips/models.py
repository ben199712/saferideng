import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Trip(models.Model):
    class TripStatus(models.TextChoices):
        active = "active", "Active"
        completed = "completed", "Completed"
        cancelled = "cancelled", "Cancelled"
        emergency = "emergency", "Emergency"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="trips",
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driven_trips",
    )
    passenger_name = models.CharField(max_length=120)
    passenger_phone = models.CharField(max_length=30)
    start_location = models.CharField(max_length=160)
    destination = models.CharField(max_length=160)
    trip_status = models.CharField(
        max_length=20,
        choices=TripStatus.choices,
        default=TripStatus.active,
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trip_status"]),
            models.Index(fields=["started_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["driver", "trip_status"]),
            models.Index(fields=["vehicle", "trip_status"]),
        ]

    def __str__(self):
        return f"{self.passenger_name} to {self.destination}"

    def complete(self):
        self.trip_status = self.TripStatus.completed
        self.ended_at = timezone.now()
        self.save(update_fields=["trip_status", "ended_at"])

    @property
    def is_active(self):
        return self.trip_status == self.TripStatus.active

    @property
    def is_emergency(self):
        return self.trip_status == self.TripStatus.emergency

    @property
    def is_current(self):
        return self.trip_status in (self.TripStatus.active, self.TripStatus.emergency)
