from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import User

from .forms import EmergencyContactForm, SOSAuthorityContactForm
from .models import EmergencyAlert, EmergencyContact, SOSAuthorityAccessLog, SOSAuthorityContact


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

    def log_authority_access(self, request, action, authority_contact=None):
        SOSAuthorityAccessLog.objects.create(
            admin_user=request.user,
            authority_contact=authority_contact,
            action=action,
            request_path=request.path,
            ip_address=request.META.get("REMOTE_ADDR"),
        )


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


class SOSAuthorityContactListView(AdminRequiredMixin, View):
    template_name = "emergency/sos_authority_contact_list.html"

    def get(self, request):
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.list)
        contacts = SOSAuthorityContact.objects.order_by("authority_name")
        return render(request, self.template_name, {"contacts": contacts})


class SOSAuthorityContactCreateView(AdminRequiredMixin, View):
    template_name = "emergency/sos_authority_contact_form.html"

    def get(self, request):
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.create)
        return render(request, self.template_name, {"form": SOSAuthorityContactForm()})

    def post(self, request):
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.create)
        form = SOSAuthorityContactForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        contact = form.save()
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.create, authority_contact=contact)
        messages.success(request, "SOS authority contact created.")
        return redirect("sos_authority_contact_list")


class SOSAuthorityContactUpdateView(AdminRequiredMixin, View):
    template_name = "emergency/sos_authority_contact_form.html"

    def get_contact(self, pk):
        return get_object_or_404(SOSAuthorityContact.objects.all(), pk=pk)

    def get(self, request, pk):
        contact = self.get_contact(pk)
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.update, authority_contact=contact)
        return render(request, self.template_name, {"form": SOSAuthorityContactForm(instance=contact), "contact": contact})

    def post(self, request, pk):
        contact = self.get_contact(pk)
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.update, authority_contact=contact)
        form = SOSAuthorityContactForm(request.POST, instance=contact)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "contact": contact})
        form.save()
        messages.success(request, "SOS authority contact updated.")
        return redirect("sos_authority_contact_list")


class SOSAuthorityContactDeleteView(AdminRequiredMixin, View):
    template_name = "emergency/sos_authority_contact_confirm_delete.html"

    def get_contact(self, pk):
        return get_object_or_404(SOSAuthorityContact.objects.all(), pk=pk)

    def get(self, request, pk):
        contact = self.get_contact(pk)
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.delete, authority_contact=contact)
        return render(request, self.template_name, {"contact": contact})

    def post(self, request, pk):
        contact = self.get_contact(pk)
        self.log_authority_access(request, SOSAuthorityAccessLog.Actions.delete, authority_contact=contact)
        contact.delete()
        messages.success(request, "SOS authority contact deleted.")
        return redirect("sos_authority_contact_list")
