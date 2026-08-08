from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from apps.tracking.models import LocationUpdate, TripShare
from apps.trips.models import Trip
from apps.vehicles.models import Vehicle
from drivers.models import DriverProfile

from .models import EmergencyAlert, SOSAlertDeliveryLog, SOSAuthorityAccessLog, SOSAuthorityContact


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DRIVER_PII_ENCRYPTION_KEY="test-driver-pii-key",
    SOS_SMS_PROVIDER="console",
)
class SOSAuthorityFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver = User.objects.create_user(
            email="driver.sos@example.com",
            password="password123",
            first_name="Driver",
            last_name="SOS",
            phone_number="+2348000000100",
        )
        self.admin = User.objects.create_user(
            email="admin.sos@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            phone_number="+2348000000101",
            role=User.Roles.admin,
            is_verified=True,
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            plate_number="SOS-123",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="Blue",
            year=2022,
            registered_route="Airport - City Centre",
            insurance_number="INS-SOS-123",
            verification_status=Vehicle.VerificationStatus.approved,
            is_active=True,
        )
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            passenger_name="Passenger",
            passenger_phone="+2348000000102",
            start_location="Airport",
            destination="City Centre",
        )
        DriverProfile.objects.create(
            user=self.driver,
            phone_number="+2348000000100",
            email="driver.sos@example.com",
            nin="12345678901",
            license_number="ABC12345",
        )
        self.authority = SOSAuthorityContact.objects.create(
            authority_name="Lagos Police Command",
            official_email="police@example.com",
            sms_phone_number="+2348000000199",
            physical_jurisdiction="Lagos",
            is_active=True,
        )

        self.share = TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=None)
        LocationUpdate.objects.create(trip_share=self.share, latitude="6.524379", longitude="3.379206")

    def test_only_admin_can_manage_authority_contacts(self):
        self.client.force_login(self.driver)
        response = self.client.get(reverse("sos_authority_contact_list"))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.get(reverse("sos_authority_contact_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lagos Police Command")
        self.assertTrue(SOSAuthorityAccessLog.objects.filter(admin_user=self.admin, action="list").exists())

    def test_trip_sos_sends_email_and_sms_and_logs_delivery(self):
        self.client.force_login(self.driver)
        response = self.client.post(reverse("trip_sos", kwargs={"uuid": self.trip.uuid}))
        self.assertEqual(response.status_code, 302)

        alert = EmergencyAlert.objects.get(trip=self.trip, alert_type=EmergencyAlert.AlertTypes.sos)
        self.assertTrue(alert.details_snapshot)
        self.assertIn("location", alert.details_snapshot)
        self.assertIn("trip", alert.details_snapshot)
        self.assertIn("driver", alert.details_snapshot)
        self.assertIn("vehicle", alert.details_snapshot)

        delivery_logs = SOSAlertDeliveryLog.objects.filter(alert=alert)
        self.assertGreaterEqual(delivery_logs.count(), 2)
        self.assertTrue(delivery_logs.filter(recipient_type="authority", channel="email", destination="police@example.com").exists())
        self.assertTrue(delivery_logs.filter(recipient_type="authority", channel="sms", destination="+2348000000199").exists())

        self.assertGreaterEqual(len(mail.outbox), 1)
