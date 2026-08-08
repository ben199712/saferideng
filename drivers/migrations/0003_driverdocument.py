import django.db.models.deletion
import drivers.documents
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drivers", "0002_driverprofile_safety_upgrade"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_type", models.CharField(choices=[("passport_photograph", "Passport Photograph"), ("driver_license", "Driver License"), ("nin_slip", "NIN Slip"), ("proof_of_address", "Proof of Address"), ("vehicle_registration", "Vehicle Registration"), ("union_membership_card", "Union Membership Card")], max_length=40)),
                ("file", models.FileField(storage=drivers.documents.PRIVATE_DRIVER_STORAGE, upload_to=drivers.documents.driver_document_upload_to)),
                ("original_file_name", models.CharField(max_length=255)),
                ("file_size", models.PositiveIntegerField(default=0)),
                ("mime_type", models.CharField(blank=True, max_length=120)),
                ("checksum_sha256", models.CharField(blank=True, max_length=64)),
                ("preview_kind", models.CharField(choices=[("image", "Image"), ("pdf", "PDF"), ("generic", "Generic")], default="generic", max_length=20)),
                ("backup_file_name", models.CharField(blank=True, max_length=255)),
                ("malware_scan_status", models.CharField(choices=[("pending", "Pending"), ("clean", "Clean"), ("skipped", "Skipped"), ("failed", "Failed")], default="pending", max_length=20)),
                ("malware_scan_message", models.CharField(blank=True, max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="driver_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["document_type"],
            },
        ),
        migrations.AddIndex(
            model_name="driverdocument",
            index=models.Index(fields=["user", "document_type"], name="drivers_dri_user_id_7ad19a_idx"),
        ),
        migrations.AddIndex(
            model_name="driverdocument",
            index=models.Index(fields=["uploaded_at"], name="drivers_dri_uploade_32df5f_idx"),
        ),
        migrations.AddConstraint(
            model_name="driverdocument",
            constraint=models.UniqueConstraint(fields=("user", "document_type"), name="unique_driver_document_type_per_user"),
        ),
    ]
