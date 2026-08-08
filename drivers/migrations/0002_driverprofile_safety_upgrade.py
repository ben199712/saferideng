from django.db import migrations, models
import django.core.validators

import drivers.fields
import drivers.validators


def backfill_driver_profile_contact_data(apps, schema_editor):
    DriverProfile = apps.get_model("drivers", "DriverProfile")

    for profile in DriverProfile.objects.select_related("user").all():
        update_fields = []

        # ----------------------------
        # Backfill Email
        # ----------------------------
        if not profile.email and profile.user and profile.user.email:
            email = profile.user.email.strip()

            email_exists = (
                DriverProfile.objects.exclude(pk=profile.pk)
                .filter(email=email)
                .exists()
            )

            if not email_exists:
                profile.email = email
                update_fields.append("email")

        # ----------------------------
        # Backfill Phone Number
        # ----------------------------
        if not profile.phone_number and profile.user and profile.user.phone_number:
            phone = profile.user.phone_number.strip()

            phone_exists = (
                DriverProfile.objects.exclude(pk=profile.pk)
                .filter(phone_number=phone)
                .exists()
            )

            if not phone_exists:
                profile.phone_number = phone
                update_fields.append("phone_number")

        # ----------------------------
        # Normalize License Number
        # ----------------------------
        if profile.license_number == "":
            profile.license_number = None
            update_fields.append("license_number")

        if update_fields:
            profile.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("drivers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="alternative_phone_number",
            field=drivers.fields.EncryptedCharField(
                blank=True,
                max_length=255,
                null=True,
                validators=[
                    drivers.validators.validate_e164_phone_number,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="date_of_birth",
            field=models.DateField(
                blank=True,
                null=True,
                validators=[
                    drivers.validators.validate_driver_age,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="driver_license_expiry_date",
            field=models.DateField(
                blank=True,
                db_index=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="email",
            field=models.EmailField(
                blank=True,
                db_index=True,
                max_length=254,
                null=True,
                unique=True,
                validators=[
                    drivers.validators.validate_driver_email,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("male", "Male"),
                    ("female", "Female"),
                    ("prefer_not_to_say", "Prefer not to say"),
                ],
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="lga",
            field=models.CharField(
                blank=True,
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="nationality",
            field=models.CharField(
                blank=True,
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="nin",
            field=drivers.fields.EncryptedCharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
                validators=[
                    drivers.validators.validate_nin,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="phone_number",
            field=drivers.fields.EncryptedCharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
                validators=[
                    drivers.validators.validate_e164_phone_number,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="residential_address",
            field=drivers.fields.EncryptedTextField(
                blank=True,
                null=True,
                validators=[
                    drivers.validators.validate_residential_address,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="state",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="transport_union",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="union_membership_number",
            field=models.CharField(
                blank=True,
                max_length=40,
                validators=[
                    drivers.validators.validate_union_membership_number,
                ],
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="years_of_driving_experience",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(2),
                    django.core.validators.MaxValueValidator(70),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="driverprofile",
            name="license_number",
            field=drivers.fields.EncryptedCharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
                validators=[
                    drivers.validators.validate_driver_license_number,
                ],
            ),
        ),
        migrations.RunPython(
            backfill_driver_profile_contact_data,
            migrations.RunPython.noop,
        ),
    ]