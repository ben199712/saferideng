from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import User
from apps.trips.models import Trip

from .forms import IncidentReportForm
from .models import IncidentReport


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


class IncidentReportCreateView(View):
    template_name = "reports/incident_report_form.html"

    def get_trip(self, trip_uuid):
        return get_object_or_404(
            Trip.objects.select_related("vehicle", "driver"),
            uuid=trip_uuid,
        )

    def get(self, request, trip_uuid):
        trip = self.get_trip(trip_uuid)
        return render(request, self.template_name, {"form": IncidentReportForm(), "trip": trip})

    def post(self, request, trip_uuid):
        trip = self.get_trip(trip_uuid)
        form = IncidentReportForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "trip": trip})
        report = form.save(commit=False)
        report.trip = trip
        report.save()
        messages.success(request, "Incident report submitted.")
        return redirect("trip_detail", uuid=trip.uuid)


class ReportDashboardView(AdminRequiredMixin, View):
    template_name = "reports/report_dashboard.html"

    def get(self, request):
        reports = IncidentReport.objects.select_related("trip", "trip__driver", "trip__vehicle").order_by("-created_at")
        stats = {
            "total": reports.count(),
            "open": reports.filter(status=IncidentReport.ReportStatus.open).count(),
            "closed": reports.filter(status=IncidentReport.ReportStatus.closed).count(),
            "under_review": reports.filter(status=IncidentReport.ReportStatus.under_review).count(),
        }
        return render(request, self.template_name, {"reports": reports, "stats": stats})


class IncidentReportDetailView(AdminRequiredMixin, View):
    template_name = "reports/incident_report_detail.html"

    def get(self, request, uuid):
        report = get_object_or_404(
            IncidentReport.objects.select_related("trip", "trip__driver", "trip__vehicle"),
            uuid=uuid,
        )
        return render(request, self.template_name, {"report": report})


class IncidentReportCloseView(AdminRequiredMixin, View):
    def post(self, request, uuid):
        report = get_object_or_404(IncidentReport.objects.select_related("trip"), uuid=uuid)
        report.close()
        messages.success(request, "Incident report closed.")
        return redirect(reverse("incident_report_detail", kwargs={"uuid": report.uuid}))
