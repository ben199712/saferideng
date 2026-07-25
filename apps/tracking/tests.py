from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from apps.tracking.models import LocationUpdate, TripShare
from apps.tracking.utils import decrypt_data, encrypt_data, generate_rsa_key_pair
from apps.trips.models import Trip
from apps.vehicles.models import Vehicle


class TrackingTestMixin:
    def create_user(self, email, role=User.Roles.driver):
        return User.objects.create_user(
            email=email,
            password="StrongPass123!",
            first_name="Test",
            last_name="User",
            phone_number="08000000000",
            role=role,
            is_verified=True,
        )

    def create_vehicle(self, driver):
        return Vehicle.objects.create(
            driver=driver,
            plate_number=f"ABC-{driver.id}XY",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="Blue",
            year=2022,
            registered_route="Campus Gate - City Center",
            insurance_number=f"INS-{driver.id}",
        )

    def create_trip(self, driver):
        vehicle = self.create_vehicle(driver)
        return Trip.objects.create(
            vehicle=vehicle,
            driver=driver,
            passenger_name="Passenger Example",
            passenger_phone="08011112222",
            start_location="University Main Gate",
            destination="City Center",
        )


class TrackingCryptoTests(TestCase):
    def test_encrypt_and_decrypt_round_trip(self):
        private_key, public_key = generate_rsa_key_pair()
        encrypted = encrypt_data("9.12345,7.54321", public_key)

        self.assertNotEqual(encrypted, "9.12345,7.54321")
        self.assertEqual(decrypt_data(encrypted, private_key), "9.12345,7.54321")


class TrackingViewTests(TrackingTestMixin, TestCase):
    def setUp(self):
        self.driver = self.create_user("driver@example.com")
        self.receiver = self.create_user("receiver@example.com")
        self.outsider = self.create_user("outsider@example.com")
        self.trip = self.create_trip(self.driver)

    def test_driver_can_create_trip_share(self):
        self.client.force_login(self.driver)

        response = self.client.post(
            reverse("tracking:create", kwargs={"trip_id": self.trip.id}),
            {"receiver_email": self.receiver.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TripShare.objects.count(), 1)
        payload = response.json()
        self.assertIn("share_url", payload)
        share = TripShare.objects.get()
        self.assertEqual(share.sharer, self.driver)
        self.assertEqual(share.receiver, self.receiver)

    def test_non_driver_cannot_create_trip_share(self):
        self.client.force_login(self.receiver)

        response = self.client.post(reverse("tracking:create", kwargs={"trip_id": self.trip.id}))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TripShare.objects.count(), 0)

    def test_authorized_receiver_can_view_live_tracking_page(self):
        share = TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=self.receiver)
        LocationUpdate.objects.create(
            trip_share=share,
            latitude=9.123456,
            longitude=7.654321,
            accuracy=8.0,
            speed=5.5,
        )
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("tracking:view", kwargs={"share_id": share.id}))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("tracking-map", content)
        self.assertIn("leaflet.css", content)
        self.assertIn("/ws/tracking/", content)
        self.assertIn("playback-slider", content)
        self.assertIn("Toggle Geofence", content)

    def test_unauthorized_user_gets_permission_denied(self):
        share = TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=self.receiver)
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("tracking:view", kwargs={"share_id": share.id}))

        self.assertEqual(response.status_code, 403)

    def test_share_list_shows_user_related_shares(self):
        TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=self.receiver)
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("tracking:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tracking Shares")
        self.assertContains(response, self.driver.email)

    def test_live_tracking_template_contains_responsive_layout_hooks(self):
        share = TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=self.receiver)
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("tracking:view", kwargs={"share_id": share.id}))

        self.assertContains(response, "xl:grid-cols-[380px_minmax(0,1fr)]")
        self.assertContains(response, "h-[420px] sm:h-[520px] lg:h-[680px]")
        self.assertContains(response, "preferCanvas")
