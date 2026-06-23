import uuid

from django.db import models


class IncidentReport(models.Model):
    class ReportTypes(models.TextChoices):
        suspicious_driver = "suspicious_driver", "Suspicious Driver"
        fake_qr = "fake_qr", "Fake QR"
        robbery = "robbery", "Robbery"
        harassment = "harassment", "Harassment"
        other = "other", "Other"

    class ReportStatus(models.TextChoices):
        open = "open", "Open"
        under_review = "under_review", "Under Review"
        closed = "closed", "Closed"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="incident_reports",
    )
    report_type = models.CharField(
        max_length=30,
        choices=ReportTypes.choices,
        db_index=True,
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.open,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["report_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["trip", "status"]),
        ]

    def __str__(self):
        return f"Report {self.uuid} - {self.get_report_type_display()}"

    def close(self):
        self.status = self.ReportStatus.closed
        self.save(update_fields=["status"])
