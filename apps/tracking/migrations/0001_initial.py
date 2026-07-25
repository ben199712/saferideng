from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('trips', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TripShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('share_secret', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('sharer_public_key', models.TextField(blank=True, null=True)),
                ('receiver_public_key', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='active', max_length=20)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='received_trips', to=settings.AUTH_USER_MODEL)),
                ('sharer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_trips', to=settings.AUTH_USER_MODEL)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares', to='trips.trip')),
            ],
        ),
        migrations.CreateModel(
            name='LocationUpdate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('encrypted_data', models.TextField(blank=True, null=True)),
                ('accuracy', models.FloatField(blank=True, null=True)),
                ('speed', models.FloatField(blank=True, null=True)),
                ('heading', models.FloatField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('is_gps_signal_lost', models.BooleanField(default=False)),
                ('trip_share', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='tracking.tripshare')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['trip_share', 'timestamp'], name='apps_tracking_locationtrip_share_timestamp_2008a2_idx')],
            },
        ),
    ]
