from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="vin",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
