from django.urls import path

from .views import (
    AdminVehicleActionView,
    AdminVehicleDashboardView,
    AdminVehicleDetailView,
    AdminVehicleDownloadView,
    DriverVehicleCreateView,
    DriverVehicleDownloadView,
    DriverVehicleListView,
    DriverVehicleUpdateView,
    VehicleVerificationView,
)

urlpatterns = [
    path("driver/vehicles/", DriverVehicleListView.as_view(), name="driver_vehicle_list"),
    path("driver/vehicles/create/", DriverVehicleCreateView.as_view(), name="driver_vehicle_create"),
    path("driver/vehicles/<uuid>/edit/", DriverVehicleUpdateView.as_view(), name="driver_vehicle_edit"),
    path("driver/vehicles/<uuid>/download-qr/", DriverVehicleDownloadView.as_view(), name="driver_vehicle_download_qr"),
    path("verify/<uuid:token>/", VehicleVerificationView.as_view(), name="verify_vehicle"),
    path("dashboard/vehicles/", AdminVehicleDashboardView.as_view(), name="admin_vehicle_dashboard"),
    path("dashboard/vehicles/<uuid>/", AdminVehicleDetailView.as_view(), name="admin_vehicle_detail"),
    path("dashboard/vehicles/<uuid>/action/", AdminVehicleActionView.as_view(), name="admin_vehicle_action"),
    path("dashboard/vehicles/<uuid>/download-qr/", AdminVehicleDownloadView.as_view(), name="admin_vehicle_download_qr"),
]
