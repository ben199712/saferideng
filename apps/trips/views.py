from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import User
from apps.emergency.models import EmergencyAlert
from apps.reports.models import IncidentReport
from apps.vehicles.models import VehicleQRCode

from .forms import TripEndForm, TripStartForm
from .models import Trip
from .services import (
    active_alert_count_for_trip,
    build_share_trip_url,
    build_trip_share_message,
    build_trip_url,
    create_trip_from_vehicle,
    open_report_count_for_trip,
    trigger_sos_alert,
)


def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.role in (User.Roles.super_admin, User.Roles.admin)
    )


class AdminRequiredMixin:
    @method_decorator(user_passes_test(is_admin_user))
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TripAccessMixin:
    def get_trip(self, request, uuid):
        trip = get_object_or_404(
            Trip.objects.select_related("vehicle", "driver", "vehicle__driver"),
            uuid=uuid,
        )
        if is_admin_user(request.user):
            return trip
        if request.user.is_authenticated and (
            trip.driver_id == request.user.id
            or trip.passenger_phone == request.user.phone_number
            or trip.passenger_name.lower() == request.user.get_full_name().lower()
        ):
            return trip
        if not request.user.is_authenticated and trip.trip_status == Trip.TripStatus.active:
            return trip
        raise PermissionDenied


class TripStartView(View):
    template_name = "trips/trip_start.html"

    def get_vehicle_from_qr(self, token):
        qr_code = (
            VehicleQRCode.objects.select_related("vehicle__driver")
            .filter(token=token, is_active=True)
            .first()
        )
        if qr_code is None or not qr_code.vehicle.is_verified:
            raise PermissionDenied
        return qr_code.vehicle

    def get(self, request, token):
        vehicle = self.get_vehicle_from_qr(token)
        form = TripStartForm(initial={"start_location": vehicle.registered_route})
        return render(request, self.template_name, {"form": form, "vehicle": vehicle})

    def post(self, request, token):
        vehicle = self.get_vehicle_from_qr(token)
        form = TripStartForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "vehicle": vehicle})

        trip = create_trip_from_vehicle(
            vehicle=vehicle,
            passenger_name=form.cleaned_data["passenger_name"],
            passenger_phone=form.cleaned_data["passenger_phone"],
            destination=form.cleaned_data["destination"],
            start_location=form.cleaned_data["start_location"],
        )
        messages.success(request, "Trip started. You can track and share it safely.")
        return redirect("trip_detail", uuid=trip.uuid)


class TripTrackingView(TripAccessMixin, View):
    template_name = "trips/trip_tracking.html"

    def get(self, request, uuid):
        trip = self.get_trip(request, uuid)
        active_alerts = trip.alerts.filter(status=EmergencyAlert.AlertStatus.active).order_by("-created_at")[:5]
        reports = trip.incident_reports.order_by("-created_at")[:5]
        emergency_contacts = []
        if request.user.is_authenticated:
            emergency_contacts = list(
                request.user.emergency_contacts.order_by("created_at")
            )
        return render(
            request,
            self.template_name,
            {
                "trip": trip,
                "active_alerts": active_alerts,
                "reports": reports,
                "emergency_contacts": emergency_contacts,
                "share_url": build_share_trip_url(request, trip.uuid),
                "tracking_url": build_trip_url(request, trip.uuid),
                "emergency_alert_count": active_alert_count_for_trip(trip),
                "open_report_count": open_report_count_for_trip(trip),
            },
        )


class TripShareView(TripAccessMixin, View):
    template_name = "trips/trip_share.html"

    def get(self, request, uuid):
        trip = self.get_trip(request, uuid)
        share_url = build_share_trip_url(request, trip.uuid)
        message = build_trip_share_message(request, trip)
        return render(
            request,
            self.template_name,
            {
                "trip": trip,
                "share_url": share_url,
                "message": message,
                "whatsapp_url": f"https://wa.me/?text={quote(message)}",
                "sms_url": f"sms:?&body={quote(message)}",
            },
        )


class TripSosView(TripAccessMixin, View):
    def post(self, request, uuid):
        trip = self.get_trip(request, uuid)
        alert = trigger_sos_alert(
            trip=trip,
            alert_type=EmergencyAlert.AlertTypes.sos,
            message="SOS alert triggered from the trip tracking page.",
            triggered_by=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, "Emergency alert sent to SafeRide responders.")
        return redirect("trip_sos_confirmation", uuid=alert.uuid)


class TripSosConfirmationView(View):
    template_name = "trips/trip_sos_confirmation.html"

    def get(self, request, uuid):
        alert = get_object_or_404(
            EmergencyAlert.objects.select_related("trip", "trip__driver", "trip__vehicle"),
            uuid=uuid,
        )
        return render(request, self.template_name, {"alert": alert})


class TripEndView(TripAccessMixin, View):
    def post(self, request, uuid):
        trip = self.get_trip(request, uuid)
        if trip.trip_status not in (Trip.TripStatus.active, Trip.TripStatus.emergency):
            messages.warning(request, "Only active or emergency trips can be ended.")
            return redirect("trip_detail", uuid=trip.uuid)

        form = TripEndForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Confirm that you want to end this trip.")
            return redirect("trip_detail", uuid=trip.uuid)

        trip.complete()
        messages.success(request, "Trip ended successfully.")
        return redirect("my_trips")


@method_decorator(login_required, name="dispatch")
class MyTripsView(View):
    template_name = "trips/my_trips.html"

    def get(self, request):
        if is_admin_user(request.user):
            trips = Trip.objects.select_related("vehicle", "driver").all()
        elif request.user.role == User.Roles.driver:
            trips = Trip.objects.select_related("vehicle", "driver").filter(driver=request.user)
        else:
            trips = Trip.objects.select_related("vehicle", "driver").filter(passenger_phone=request.user.phone_number)

        current_trips = trips.filter(trip_status__in=[Trip.TripStatus.active, Trip.TripStatus.emergency])
        past_trips = trips.exclude(trip_status__in=[Trip.TripStatus.active, Trip.TripStatus.emergency])
        active_alerts = EmergencyAlert.objects.filter(
            trip__in=current_trips,
            status=EmergencyAlert.AlertStatus.active,
        ).count()
        reports = IncidentReport.objects.filter(trip__in=trips)
        return render(
            request,
            self.template_name,
            {
                "current_trips": current_trips,
                "past_trips": past_trips,
                "reports": reports.order_by("-created_at")[:10],
                "active_alerts": active_alerts,
                "emergency_status": "Active emergency" if active_alerts else "No active emergency",
            },
        )
