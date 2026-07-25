from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
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

    def test_public_share_url_points_to_trip_detail(self):
        request = self.factory.get("/")
        request.user = self.driver

        share_url = build_share_trip_url(request, self.trip.uuid)

        self.assertIn(reverse("trip_detail", kwargs={"uuid": self.trip.uuid}), share_url)
        self.assertNotIn(reverse("trip_share", kwargs={"uuid": self.trip.uuid}), share_url)

    def test_trip_share_page_displays_live_tracking_link(self):
        response = self.client.get(reverse("trip_share", kwargs={"uuid": self.trip.uuid}))

        self.assertEqual(response.status_code, 200)
        expected_tracking_path = reverse("trip_detail", kwargs={"uuid": self.trip.uuid})
        self.assertContains(response, expected_tracking_path)
        self.assertNotContains(response, reverse("trip_share", kwargs={"uuid": self.trip.uuid}))
