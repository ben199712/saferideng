from django.urls import path

from .views import (
    DriverDocumentDeleteView,
    DriverDocumentFileView,
    DriverDocumentUploadView,
    DriverProfileView,
    DriverPublicProfileView,
    DriverRegistrationView,
)

urlpatterns = [
    path("profile/", DriverProfileView.as_view(), name="driver_profile"),
    path("driver/<uuid:driver_uuid>/vehicle/<uuid:vehicle_uuid>/", DriverPublicProfileView.as_view(), name="driver_public_profile"),
    path("register/", DriverRegistrationView.as_view(), name="driver_register"),
    path("documents/upload/", DriverDocumentUploadView.as_view(), name="driver_document_upload"),
    path("documents/<int:pk>/file/", DriverDocumentFileView.as_view(), name="driver_document_file"),
    path("documents/<int:pk>/delete/", DriverDocumentDeleteView.as_view(), name="driver_document_delete"),
]

