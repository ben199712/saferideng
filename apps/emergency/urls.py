from django.urls import path

from .views import (
    EmergencyAlertDetailView,
    EmergencyAlertResolveView,
    EmergencyContactCreateView,
    EmergencyContactDeleteView,
    EmergencyContactListView,
    EmergencyContactUpdateView,
    EmergencyDashboardView,
)

urlpatterns = [
    path("emergency/contacts/", EmergencyContactListView.as_view(), name="emergency_contact_list"),
    path("emergency/contacts/create/", EmergencyContactCreateView.as_view(), name="emergency_contact_create"),
    path("emergency/contacts/<int:pk>/edit/", EmergencyContactUpdateView.as_view(), name="emergency_contact_update"),
    path("emergency/contacts/<int:pk>/delete/", EmergencyContactDeleteView.as_view(), name="emergency_contact_delete"),
    path("dashboard/emergency/", EmergencyDashboardView.as_view(), name="emergency_dashboard"),
    path("dashboard/emergency/<uuid:uuid>/", EmergencyAlertDetailView.as_view(), name="emergency_alert_detail"),
    path("dashboard/emergency/<uuid:uuid>/resolve/", EmergencyAlertResolveView.as_view(), name="emergency_alert_resolve"),
]
