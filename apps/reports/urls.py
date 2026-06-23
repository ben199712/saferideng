from django.urls import path

from .views import (
    IncidentReportCloseView,
    IncidentReportCreateView,
    IncidentReportDetailView,
    ReportDashboardView,
)

urlpatterns = [
    path("report/create/<uuid:trip_uuid>/", IncidentReportCreateView.as_view(), name="incident_report_create"),
    path("dashboard/reports/", ReportDashboardView.as_view(), name="report_dashboard"),
    path("dashboard/reports/<uuid:uuid>/", IncidentReportDetailView.as_view(), name="incident_report_detail"),
    path("dashboard/reports/<uuid:uuid>/close/", IncidentReportCloseView.as_view(), name="incident_report_close"),
]
