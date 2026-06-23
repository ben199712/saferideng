from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.emergency.models import EmergencyAlert
from apps.reports.models import IncidentReport

from .models import Trip


def build_trip_url(request, uuid):
    return request.build_absolute_uri(reverse("trip_detail", kwargs={"uuid": str(uuid)}))


def build_share_trip_url(request, uuid):
    return request.build_absolute_uri(reverse("trip_share", kwargs={"uuid": str(uuid)}))


def build_trip_share_message(request, trip):
    share_url = build_share_trip_url(request, trip.uuid)
    return (
        "I just boarded a SafeRide verified vehicle.\n\n"
        f"Driver: {trip.driver.full_name}\n"
        f"Plate Number: {trip.vehicle.plate_number}\n"
        "Track this trip:\n"
        f"{share_url}"
    )


@transaction.atomic
def create_trip_from_vehicle(vehicle, passenger_name, passenger_phone, destination, start_location=None):
    return Trip.objects.create(
        vehicle=vehicle,
        driver=vehicle.driver,
        passenger_name=passenger_name,
        passenger_phone=passenger_phone,
        start_location=start_location or vehicle.registered_route,
        destination=destination,
        trip_status=Trip.TripStatus.active,
    )


@transaction.atomic
def trigger_sos_alert(trip, alert_type=EmergencyAlert.AlertTypes.sos, message="", triggered_by=None):
    trip.trip_status = Trip.TripStatus.emergency
    trip.save(update_fields=["trip_status"])
    return EmergencyAlert.objects.create(
        trip=trip,
        alert_type=alert_type,
        triggered_by=triggered_by,
        status=EmergencyAlert.AlertStatus.active,
        message=message,
    )


@transaction.atomic
def resolve_emergency_alert(alert):
    alert.resolve()


@transaction.atomic
def close_incident_report(report):
    report.close()


def active_alert_count_for_trip(trip):
    return trip.alerts.filter(status=EmergencyAlert.AlertStatus.active).count()


def open_report_count_for_trip(trip):
    return trip.incident_reports.filter(status__in=[
        IncidentReport.ReportStatus.open,
        IncidentReport.ReportStatus.under_review,
    ]).count()
