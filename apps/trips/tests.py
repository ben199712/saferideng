from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from apps.tracking.models import TripShare
from apps.trips.models import Trip
from apps.trips.services import build_share_trip_url
from apps.vehicles.models import Vehicle


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class TripShareFlowTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            email="driver.trip@example.com",
            password="password123",
            first_name="Driver",
            last_name="Trip",
            phone_number="+2348000000090",
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            plate_number="TRIP-123",
            vehicle_type=Vehicle.VehicleTypes.taxi,
            vehicle_make="Toyota",
            vehicle_model="Corolla",
            vehicle_color="Black",
            year=2022,
            registered_route="Main Gate - Town",
            insurance_number="INS-TRIP-123",
            verification_status=Vehicle.VerificationStatus.approved,
            is_active=True,
        )
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            driver=self.driver,
            passenger_name="Passenger One",
            passenger_phone="+2348000000091",
            start_location="Main Gate",
            destination="Town",
        )
        self.factory = RequestFactory()
        self.client = Client()

    def test_public_shayour-resend-api-key-here(self):
        request = self.factory.get("/")
        request.user = self.driver

        share_url = build_share_trip_url(request, self.trip.uuid)
        share = TripShare.objects.get(trip=self.trip, receiver=None)

        self.assertIn(reverse("tracking:view", kwargs={"share_id": share.id}), share_url)
        self.assertIn(f"secret={share.share_secret}", share_url)
        self.assertNotIn(reverse("trip_share", kwargs={"uuid": self.trip.uuid}), share_url)

    def test_trip_shayour-resend-api-key-here(self):
        response = self.client.get(reverse("trip_share", kwargs={"uuid": self.trip.uuid}))
        share = TripShare.objects.get(trip=self.trip, receiver=None)

        self.assertEqual(response.status_code, 200)
        expected_tracking_path = reverse("tracking:view", kwargs={"share_id": share.id})
        self.assertContains(response, expected_tracking_path)
        self.assertNotContains(response, reverse("trip_share", kwargs={"uuid": self.trip.uuid}))

    def test_trip_tracking_page_embeds_background_broadcast_script(self):
        share = TripShare.objects.create(trip=self.trip, sharer=self.driver, receiver=None)
        session = self.client.session
        session[f"trip_broadcast_{self.trip.uuid}"] = str(share.broadcaster_token)
        session.save()

        response = self.client.get(reverse("trip_detail", kwargs={"uuid": self.trip.uuid}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(share.id))
        self.assertContains(response, str(share.broadcaster_token))
        self.assertContains(response, "setInterval(pollLocation, 10000)")
