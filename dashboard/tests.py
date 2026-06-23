from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from drivers.models import DriverProfile


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardAuthorizationTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            email="driver@example.com",
            password="password123",
            first_name="Driver",
            last_name="User",
            phone_number="+2348000000000",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            phone_number="+2348000000001",
            role=User.Roles.admin,
            is_staff=True,
        )
        self.profile = DriverProfile.objects.create(
            user=self.driver,
            license_number="ABC123456",
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_plate_number="ABC-123-XY",
            verification_status=DriverProfile.VerificationStatus.pending,
        )

    def test_driver_cannot_access_dashboard(self):
        client = Client()
        client.force_login(self.driver)

        response = client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 302)

    def test_driver_cannot_approve_profile(self):
        client = Client()
        client.force_login(self.driver)

        response = client.post(
            reverse("driver_approval", kwargs={"pk": self.profile.pk}),
            {"action": "approve"},
        )

        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, DriverProfile.VerificationStatus.pending)

    def test_admin_can_approve_profile(self):
        client = Client()
        client.force_login(self.admin)

        response = client.post(
            reverse("driver_approval", kwargs={"pk": self.profile.pk}),
            {"action": "approve"},
        )

        self.profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_home"))
        self.assertEqual(self.profile.verification_status, DriverProfile.VerificationStatus.verified)
        self.assertTrue(self.profile.is_approved)
