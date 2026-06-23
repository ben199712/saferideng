from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import User

from .forms import EmergencyContactForm
from .models import EmergencyAlert, EmergencyContact


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


class EmergencyContactListView(View):
    template_name = "emergency/emergency_contact_list.html"

    def get(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied
        contacts = request.user.emergency_contacts.order_by("created_at")
        return render(request, self.template_name, {"contacts": contacts})


class EmergencyContactCreateView(View):
    template_name = "emergency/emergency_contact_form.html"

    def get(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied
        return render(request, self.template_name, {"form": EmergencyContactForm()})

    def post(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied
        form = EmergencyContactForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        contact = form.save(commit=False)
        contact.user = request.user
        contact.save()
        messages.success(request, "Emergency contact added.")
        return redirect("emergency_contact_list")


class EmergencyContactUpdateView(View):
    template_name = "emergency/emergency_contact_form.html"

    def get_contact(self, request, pk):
        return get_object_or_404(EmergencyContact.objects.filter(user=request.user), pk=pk)

    def get(self, request, pk):
        if not request.user.is_authenticated:
            raise PermissionDenied
        contact = self.get_contact(request, pk)
        return render(request, self.template_name, {"form": EmergencyContactForm(instance=contact), "contact": contact})

    def post(self, request, pk):
        if not request.user.is_authenticated:
            raise PermissionDenied
        contact = self.get_contact(request, pk)
        form = EmergencyContactForm(request.POST, instance=contact)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "contact": contact})
        form.save()
        messages.success(request, "Emergency contact updated.")
        return redirect("emergency_contact_list")


class EmergencyContactDeleteView(View):
    template_name = "emergency/emergency_contact_confirm_delete.html"

    def get_contact(self, request, pk):
        return get_object_or_404(EmergencyContact.objects.filter(user=request.user), pk=pk)

    def get(self, request, pk):
        if not request.user.is_authenticated:
            raise PermissionDenied
        contact = self.get_contact(request, pk)
        return render(request, self.template_name, {"contact": contact})

    def post(self, request, pk):
        if not request.user.is_authenticated:
            raise PermissionDenied
        contact = self.get_contact(request, pk)
        contact.delete()
        messages.success(request, "Emergency contact deleted.")
        return redirect("emergency_contact_list")


class EmergencyDashboardView(AdminRequiredMixin, View):
    template_name = "emergency/emergency_dashboard.html"

    def get(self, request):
        alerts = EmergencyAlert.objects.select_related(
            "trip",
            "trip__driver",
            "trip__vehicle",
            "triggered_by",
        ).order_by("-created_at")
        stats = {
            "total": alerts.count(),
            "active": alerts.filter(status=EmergencyAlert.AlertStatus.active).count(),
            "resolved": alerts.filter(status=EmergencyAlert.AlertStatus.resolved).count(),
        }
        return render(request, self.template_name, {"alerts": alerts, "stats": stats})


class EmergencyAlertDetailView(AdminRequiredMixin, View):
    template_name = "emergency/emergency_alert_detail.html"

    def get(self, request, uuid):
        alert = get_object_or_404(
            EmergencyAlert.objects.select_related(
                "trip",
                "trip__driver",
                "trip__vehicle",
                "triggered_by",
            ),
            uuid=uuid,
        )
        return render(request, self.template_name, {"alert": alert})


class EmergencyAlertResolveView(AdminRequiredMixin, View):
    def post(self, request, uuid):
        alert = get_object_or_404(EmergencyAlert.objects.select_related("trip"), uuid=uuid)
        alert.resolve()
        messages.success(request, "Emergency alert resolved.")
        return redirect(reverse("emergency_alert_detail", kwargs={"uuid": alert.uuid}))
