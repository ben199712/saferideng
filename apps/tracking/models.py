from django.db import models
import uuid
from django.conf import settings
from apps.trips.models import Trip


class TripShare(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='shares')
    sharer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_trips')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_trips', null=True, blank=True)
    share_secret = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    broadcaster_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sharer_public_key = models.TextField(null=True, blank=True)
    receiver_public_key = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Share for Trip {self.trip.id}: {self.sharer.email}"


class LocationUpdate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip_share = models.ForeignKey(TripShare, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    encrypted_data = models.TextField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_gps_signal_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['trip_share', 'timestamp']),
        ]

    def __str__(self):
        return f"Location for {self.trip_share.id} at {self.timestamp}"
