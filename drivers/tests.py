from datetime import date, timedelta
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from drivers.models import DriverDocument, DriverProfile


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    DRIVER_PII_ENCRYPTION_KEY="test-driver-pii-key",
)
class DriverProfileViewTests(TestCase):
    def setUp(self):
        self.temp_private = TemporaryDirectory()
        self.temp_backup = TemporaryDirectory()
        self.override = override_settings(
            PRIVATE_DRIVER_DOCUMENTS_ROOT=self.temp_private.name,
            PRIVATE_DRIVER_DOCUMENTS_BACKUP_ROOT=self.temp_backup.name,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.temp_private.cleanup)
        self.addCleanup(self.temp_backup.cleanup)

        self.user = User.objects.create_user(
            email="driver@example.com",
            password="password123",
            first_name="Driver",
            last_name="User",
            phone_number="+2348000000000",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def upload_required_documents(self):
        required_documents = {
            "passport_photograph": SimpleUploadedFile("passport.png", PNG_BYTES, content_type="image/png"),
            "driver_license": SimpleUploadedFile("license.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf"),
            "nin_slip": SimpleUploadedFile("nin-slip.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf"),
            "proof_of_address": SimpleUploadedFile("address.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf"),
        }
        for document_type, file_obj in required_documents.items():
            response = self.client.post(
                reverse("driver_document_upload"),
                {"document_type": document_type, "file": file_obj},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 200)

    def valid_payload(self, **overrides):
        payload = {
            "date_of_birth": (date.today() - timedelta(days=30 * 365)).isoformat(),
            "gender": "male",
            "phone_number": "+2348012345678",
            "alternative_phone_number": "+2348098765432",
            "email": "driver@example.com",
            "residential_address": "12 SafeRide Avenue, Ikeja, Lagos",
            "state": "Lagos",
            "lga": "Ikeja",
            "nationality": "Nigeria",
            "nin": "12345678901",
            "license_number": "ABC12345",
            "driver_license_expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "transport_union": "nurtw",
            "union_membership_number": "NURTW-12345",
            "years_of_driving_experience": 8,
            "vehicle_make": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_plate_number": "ABC-123-XY",
        }
        payload.update(overrides)
        return payload

    def test_driver_can_submit_profile(self):
        self.upload_required_documents()
        response = self.client.post(
            reverse("driver_register"),
            self.valid_payload(),
        )

        profile = DriverProfile.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("driver_profile"))
        self.assertEqual(profile.license_number, "ABC12345")
        self.assertEqual(profile.phone_number, "+2348012345678")
        self.assertEqual(profile.state, "Lagos")
        self.assertEqual(profile.lga, "Ikeja")
        self.assertEqual(profile.nin, "12345678901")
        self.assertEqual(profile.vehicle_make, "Toyota")
        self.assertEqual(profile.vehicle_model, "Corolla")
        self.assertEqual(profile.vehicle_plate_number, "ABC-123-XY")
        self.assertEqual(profile.verification_status, DriverProfile.VerificationStatus.pending)
        self.assertFalse(profile.is_approved)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "+2348012345678")

    def test_driver_register_page_loads(self):
        response = self.client.get(reverse("driver_register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Driver Registration")
        self.assertContains(response, "Date of Birth")
        self.assertContains(response, "National Identification Number")
        self.assertContains(response, "Select LGA")

    def test_driver_profile_update_link_points_to_register_route(self):
        response = self.client.get(reverse("driver_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/drivers/register/"')

    def test_driver_can_update_existing_profile(self):
        DriverProfile.objects.create(
            user=self.user,
            license_number="ABC12345",
            phone_number="+2348011111111",
            email="driver@example.com",
            nin="12345678901",
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_plate_number="ABC-123-XY",
            verification_status=DriverProfile.VerificationStatus.verified,
            is_approved=True,
        )
        self.upload_required_documents()

        response = self.client.post(
            reverse("driver_register"),
            self.valid_payload(
                vehicle_model="Camry",
                vehicle_plate_number="XYZ-789-AB",
                phone_number="+2348011111111",
                nin="12345678901",
            ),
        )

        profile = DriverProfile.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.vehicle_model, "Camry")
        self.assertEqual(profile.vehicle_plate_number, "XYZ-789-AB")
        self.assertEqual(profile.verification_status, DriverProfile.VerificationStatus.pending)
        self.assertFalse(profile.is_approved)

    def test_driver_cannot_submit_profile_without_required_documents(self):
        response = self.client.post(
            reverse("driver_register"),
            self.valid_payload(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload the required documents before submitting")
        self.assertFalse(DriverProfile.objects.filter(user=self.user).exists())

    def test_underage_driver_is_rejected(self):
        response = self.client.post(
            reverse("driver_register"),
            self.valid_payload(date_of_birth=(date.today() - timedelta(days=20 * 365)).isoformat()),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Drivers must be at least 21 years old.")

    def test_invalid_lga_for_state_is_rejected(self):
        response = self.client.post(
            reverse("driver_register"),
            self.valid_payload(state="Lagos", lga="Kuje"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid LGA for the chosen state.")

    def test_sensitive_driver_fields_are_encrypted(self):
        self.client.post(reverse("driver_register"), self.valid_payload())

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT phone_number, alternative_phone_number, residential_address, nin, license_number FROM drivers_driverprofile WHERE user_id = %s",
                [self.user.id],
            )
            phone_number, alt_phone, address, nin, license_number = cursor.fetchone()

        self.assertTrue(phone_number.startswith("enc1:"))
        self.assertTrue(alt_phone.startswith("enc1:"))
        self.assertTrue(address.startswith("enc1:"))
        self.assertTrue(nin.startswith("enc1:"))
        self.assertTrue(license_number.startswith("enc1:"))
        self.assertNotEqual(phone_number, "+2348012345678")


@override_settings(DRIVER_PII_ENCRYPTION_KEY="test-driver-pii-key")
class DriverProfileModelValidationTests(TestCase):
    def test_experience_cannot_exceed_age_window(self):
        user = User.objects.create_user(
            email="model@example.com",
            password="password123",
            first_name="Model",
            last_name="Driver",
            phone_number="+2348000000009",
        )
        profile = DriverProfile(
            user=user,
            date_of_birth=date.today() - timedelta(days=22 * 365),
            gender="male",
            phone_number="+2348111111111",
            email="model@example.com",
            residential_address="12 SafeRide Avenue, Lagos",
            state="Lagos",
            lga="Ikeja",
            nationality="Nigeria",
            nin="12345678901",
            license_number="ABC12345",
            driver_license_expiry_date=date.today() + timedelta(days=300),
            transport_union="nurtw",
            union_membership_number="NURTW-44444",
            years_of_driving_experience=10,
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\x0f"
    b"\x00\x01\x01\x01\x00\x18\xdd\x8d\xe1\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    DRIVER_PII_ENCRYPTION_KEY="test-driver-pii-key",
    DRIVER_DOCUMENT_MALWARE_SCAN_ENABLED=False,
)
class DriverDocumentUploadTests(TestCase):
    def setUp(self):
        self.temp_private = TemporaryDirectory()
        self.temp_backup = TemporaryDirectory()
        self.override = override_settings(
            PRIVATE_DRIVER_DOCUMENTS_ROOT=self.temp_private.name,
            PRIVATE_DRIVER_DOCUMENTS_BACKUP_ROOT=self.temp_backup.name,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.temp_private.cleanup)
        self.addCleanup(self.temp_backup.cleanup)

        self.driver = User.objects.create_user(
            email="docs@example.com",
            password="password123",
            first_name="Doc",
            last_name="Driver",
            phone_number="+2348000000022",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            first_name="Other",
            last_name="User",
            phone_number="+2348000000023",
        )
        self.client.force_login(self.driver)

    def make_png(self, name="passport.png"):
        return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")

    def make_pdf(self, name="proof.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF", content_type="application/pdf")

    def test_driver_register_page_shows_document_section(self):
        response = self.client.get(reverse("driver_register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Supporting Documents")
        self.assertContains(response, "Passport Photograph")
        self.assertContains(response, "Proof of Address")

    def test_driver_can_upload_document(self):
        response = self.client.post(
            reverse("driver_document_upload"),
            {"document_type": "passport_photograph", "file": self.make_png()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        document = DriverDocument.objects.get(user=self.driver, document_type="passport_photograph")
        self.assertEqual(document.preview_kind, DriverDocument.PreviewKind.image)
        self.assertEqual(document.malware_scan_status, DriverDocument.ScanStatus.skipped)
        self.assertTrue(document.backup_file_name)

    def test_upload_replaces_existing_document(self):
        self.client.post(
            reverse("driver_document_upload"),
            {"document_type": "proof_of_address", "file": self.make_pdf("old-proof.pdf")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.post(
            reverse("driver_document_upload"),
            {"document_type": "proof_of_address", "file": self.make_pdf("new-proof.pdf")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        document = DriverDocument.objects.get(user=self.driver, document_type="proof_of_address")
        self.assertEqual(document.original_file_name, "new-proof.pdf")

    def test_driver_can_delete_uploaded_document(self):
        self.client.post(
            reverse("driver_document_upload"),
            {"document_type": "driver_license", "file": self.make_pdf("license.pdf")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        document = DriverDocument.objects.get(user=self.driver, document_type="driver_license")

        response = self.client.post(reverse("driver_document_delete", kwargs={"pk": document.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(DriverDocument.objects.filter(pk=document.pk).exists())

    def test_uploaded_document_file_is_protected(self):
        self.client.post(
            reverse("driver_document_upload"),
            {"document_type": "nin_slip", "file": self.make_pdf("nin-slip.pdf")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        document = DriverDocument.objects.get(user=self.driver, document_type="nin_slip")

        owner_response = self.client.get(reverse("driver_document_file", kwargs={"pk": document.pk}))
        self.assertEqual(owner_response.status_code, 200)

        self.client.force_login(self.other_user)
        other_response = self.client.get(reverse("driver_document_file", kwargs={"pk": document.pk}))
        self.assertEqual(other_response.status_code, 404)

    def test_invalid_file_type_is_rejected(self):
        response = self.client.post(
            reverse("driver_document_upload"),
            {
                "document_type": "passport_photograph",
                "file": SimpleUploadedFile("bad.txt", b"not allowed", content_type="text/plain"),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(DriverDocument.objects.filter(user=self.driver, document_type="passport_photograph").exists())
