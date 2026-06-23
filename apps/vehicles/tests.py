from django.contrib.admin.sites import AdminSite
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from apps.vehicles.admin import VehicleAdmin
from apps.vehicles.models import QRScanLog, Vehicle, VehicleQRCode


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class VehicleWorkflowTests(TestCase):
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
        self.client = Client()

    def test_driver_can_create_vehicle(self):
        self.client.force_login(self.driver)

        response = self.client.post(
            reverse("driver_vehicle_create"),
            {
                "plate_number": "ABC-123-XY",
                "vehicle_type": Vehicle.VehicleTypes.taxi,
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "vehicle_color": "White",
                "year": 2022,
                "registered_route": "Airport - City Centre",
                "insurance_number": "INS-12345",
            },
        )

        vehicle = Vehicle.objects.get(plate_number="ABC-123-XY")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("driver_vehicle_list"))
        self.assertEqual(vehicle.driver, self.driver)
        self.assertEqual(vehicle.verification_status, Vehicle.VerificationStatus.pending)
        self.assertTrue(vehicle.is_active)

    def test_admin_can_approve_vehicle_and_generate_qr(self):
        vehicle = Vehicle.objects.create(
            driver=self.driver,
            plate_number="ABC-123-XY",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="White",
            year=2022,
            registered_route="Airport - City Centre",
            insurance_number="INS-12345",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_vehicle_action", kwargs={"uuid": vehicle.uuid}),
            {"action": "approve"},
        )

        vehicle.refresh_from_db()
        qr_code = VehicleQRCode.objects.get(vehicle=vehicle)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_vehicle_detail", kwargs={"uuid": vehicle.uuid}))
        self.assertEqual(vehicle.verification_status, Vehicle.VerificationStatus.approved)
        self.assertTrue(vehicle.is_active)
        self.assertIsNotNone(vehicle.approved_at)
        self.assertTrue(qr_code.is_active)
        self.assertIsNotNone(qr_code.qr_image)

    def test_public_verification_logs_scan_for_approved_vehicle(self):
        vehicle = Vehicle.objects.create(
            driver=self.driver,
            plate_number="ABC-123-XY",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="White",
            year=2022,
            registered_route="Airport - City Centre",
            insurance_number="INS-12345",
            verification_status=Vehicle.VerificationStatus.approved,
            is_active=True,
        )
        qr_code = VehicleQRCode.objects.create(vehicle=vehicle)

        response = self.client.get(reverse("verify_vehicle", kwargs={"token": qr_code.token}))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("driver_public_profile", kwargs={"driver_uuid": self.driver.uuid, "vehicle_uuid": vehicle.uuid}))
        self.assertEqual(QRScanLog.objects.count(), 1)

    def test_vehicle_admin_approval_generates_qr_code(self):
        vehicle = Vehicle.objects.create(
            driver=self.driver,
            plate_number="ABC-123-XY",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="White",
            year=2022,
            registered_route="Airport - City Centre",
            insurance_number="INS-12345",
        )
        admin_site = AdminSite()
        vehicle_admin = VehicleAdmin(Vehicle, admin_site)
        request = RequestFactory().post("/")
        request.user = self.admin

        vehicle.verification_status = Vehicle.VerificationStatus.approved
        vehicle_admin.save_model(request, vehicle, None, True)

        vehicle.refresh_from_db()
        qr_code = VehicleQRCode.objects.get(vehicle=vehicle)
        self.assertTrue(vehicle.is_active)
        self.assertIsNotNone(vehicle.approved_at)
        self.assertIsNotNone(qr_code.qr_image)
        self.assertTrue(qr_code.is_active)

    def test_driver_cannot_access_admin_vehicle_dashboard(self):
        self.client.force_login(self.driver)

        response = self.client.get(reverse("admin_vehicle_dashboard"))

        self.assertEqual(response.status_code, 403)
