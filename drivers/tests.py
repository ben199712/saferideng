from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from drivers.models import DriverProfile


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DriverProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="driver@example.com",
            password="password123",
            first_name="Driver",
            last_name="User",
            phone_number="+2348000000000",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_driver_can_submit_profile(self):
        response = self.client.post(
            reverse("driver_register"),
            {
                "license_number": "ABC123456",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "vehicle_plate_number": "ABC-123-XY",
            },
        )

        profile = DriverProfile.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("driver_profile"))
        self.assertEqual(profile.license_number, "ABC123456")
        self.assertEqual(profile.vehicle_make, "Toyota")
        self.assertEqual(profile.vehicle_model, "Corolla")
        self.assertEqual(profile.vehicle_plate_number, "ABC-123-XY")
        self.assertEqual(profile.verification_status, DriverProfile.VerificationStatus.pending)
        self.assertFalse(profile.is_approved)

    def test_driver_can_update_existing_profile(self):
        DriverProfile.objects.create(
            user=self.user,
            license_number="ABC123456",
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_plate_number="ABC-123-XY",
            verification_status=DriverProfile.VerificationStatus.verified,
            is_approved=True,
        )

        response = self.client.post(
            reverse("driver_register"),
            {
                "license_number": "ABC123456",
                "vehicle_make": "Toyota",
                "vehicle_model": "Camry",
                "vehicle_plate_number": "XYZ-789-AB",
            },
        )

        profile = DriverProfile.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.vehicle_model, "Camry")
        self.assertEqual(profile.vehicle_plate_number, "XYZ-789-AB")
        self.assertEqual(profile.verification_status, DriverProfile.VerificationStatus.pending)
        self.assertFalse(profile.is_approved)
