from django.urls import path

from .views import (
    MyTripsView,
    TripEndView,
    TripShareView,
    TripSosConfirmationView,
    TripSosView,
    TripStartView,
    TripTrackingView,
)

urlpatterns = [
    path("trip/start/<uuid:token>/", TripStartView.as_view(), name="trip_start"),
    path("trip/share/<uuid:uuid>/", TripShareView.as_view(), name="trip_share"),
    path("trip/<uuid:uuid>/sos/", TripSosView.as_view(), name="trip_sos"),
    path("trip/<uuid:uuid>/sos/confirmation/", TripSosConfirmationView.as_view(), name="trip_sos_confirmation"),
    path("trip/<uuid:uuid>/end/", TripEndView.as_view(), name="trip_end"),
    path("trip/<uuid:uuid>/", TripTrackingView.as_view(), name="trip_detail"),
    path("my-trips/", MyTripsView.as_view(), name="my_trips"),
]
