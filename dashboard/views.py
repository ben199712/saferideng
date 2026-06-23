from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import User
from drivers.models import DriverProfile


def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.role in (User.Roles.super_admin, User.Roles.admin)
    )


class AdminRequiredMixin:
    @method_decorator(user_passes_test(is_admin_user))
    def dispatch(self, *args, **kwargs):
        if not is_admin_user(self.request.user):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)


class DashboardHomeView(AdminRequiredMixin, View):
    """Unified dashboard home for SafeRide admins."""

    def get(self, request, *args, **kwargs):
        total_drivers = DriverProfile.objects.count()
        pending = DriverProfile.objects.filter(verification_status=DriverProfile.VerificationStatus.pending).count()
        verified = DriverProfile.objects.filter(verification_status=DriverProfile.VerificationStatus.verified).count()
        flagged = DriverProfile.objects.filter(verification_status=DriverProfile.VerificationStatus.flagged).count()

        pending_qs = (
            DriverProfile.objects.select_related("user")
            .filter(verification_status=DriverProfile.VerificationStatus.pending)
            .order_by("-created_at")[:10]
        )

        ctx = {
            "stats": {
                "total_drivers": total_drivers,
                "pending": pending,
                "verified": verified,
                "flagged": flagged,
            },
            "pending_drivers": pending_qs,
        }
        return render(request, "dashboard/dashboard_home.html", ctx)


class DriverApprovalView(AdminRequiredMixin, View):
    """Admin action: approve/flag driver profiles."""

    def post(self, request, *args, **kwargs):
        driver_profile = get_object_or_404(DriverProfile, pk=kwargs["pk"])
        action = request.POST.get("action")

        if action == "approve":
            driver_profile.verification_status = DriverProfile.VerificationStatus.verified
            driver_profile.is_approved = True
        elif action == "flag":
            driver_profile.verification_status = DriverProfile.VerificationStatus.flagged
            driver_profile.is_approved = False
        else:
            return redirect(reverse("dashboard_home"))

        driver_profile.save()
        messages.success(request, "Driver verification status updated.")
        return redirect(reverse("dashboard_home"))
