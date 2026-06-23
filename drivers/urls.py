from django.urls import path

from .views import DriverProfileView, DriverPublicProfileView, DriverRegistrationView

urlpatterns = [
    path("profile/", DriverProfileView.as_view(), name="driver_profile"),
    path("driver/<uuid:driver_uuid>/vehicle/<uuid:vehicle_uuid>/", DriverPublicProfileView.as_view(), name="driver_public_profile"),
    path("register/", DriverRegistrationView.as_view(), name="driver_register"),
]

