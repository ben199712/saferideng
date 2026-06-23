from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from .forms import DriverRegistrationForm
from .models import DriverProfile
from apps.vehicles.models import Vehicle, VehicleQRCode


class DriverProfileView(LoginRequiredMixin, TemplateView):
    template_name = "drivers/driver_profile.html"

    def get(self, request, *args, **kwargs):
        profile = DriverProfile.objects.filter(user=request.user).first()
        legacy_vehicle_label = ""
        if profile:
            legacy_vehicle_label = f"{profile.vehicle_make or ''} {profile.vehicle_model or ''}".strip() or "Not submitted"
        return render(
            request,
            self.template_name,
            {
                "profile": profile,
                "profile_exists": profile is not None,
                "legacy_vehicle_label": legacy_vehicle_label,
            },
        )


class DriverRegistrationView(LoginRequiredMixin, View):
    template_name = "drivers/driver_register.html"

    def get_profile(self, request):
        return DriverProfile.objects.filter(user=request.user).first()

    def get(self, request, *args, **kwargs):
        profile = self.get_profile(request)
        form = DriverRegistrationForm(instance=profile)
        return render(request, self.template_name, {"form": form, "profile": profile})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile(request)
        form = DriverRegistrationForm(request.POST, instance=profile)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "profile": profile})

        created = profile is None
        if profile is None:
            profile = DriverProfile(user=request.user)

        payload = form.to_model_payload()
        for key, value in payload.items():
            setattr(profile, key, value)
        profile.verification_status = DriverProfile.VerificationStatus.pending
        profile.is_approved = False
        profile.save()

        if created:
            messages.success(request, "Driver profile submitted. Awaiting verification.")
        else:
            messages.success(request, "Driver profile updated and resubmitted for verification.")
        return redirect("driver_profile")


class DriverPublicProfileView(View):
    template_name = "drivers/public_driver_profile.html"

    def get_state(self, vehicle):
        if vehicle.verification_status == Vehicle.VerificationStatus.rejected:
            return "rejected"
        if not vehicle.is_active:
            return "suspended"
        if vehicle.verification_status == Vehicle.VerificationStatus.approved:
            return "verified"
        return "pending"

    def get(self, request, driver_uuid, vehicle_uuid):
        vehicle = get_object_or_404(
            Vehicle.objects.select_related("driver", "qr_code"),
            driver__uuid=driver_uuid,
            uuid=vehicle_uuid,
        )
        qr_code = getattr(vehicle, "qr_code", None)
        state = self.get_state(vehicle)
        scan_count = qr_code.scan_logs.count() if qr_code else 0
        return render(
            request,
            self.template_name,
            {
                "vehicle": vehicle,
                "qr_code": qr_code,
                "state": state,
                "can_start_trip": state == "verified" and bool(qr_code and qr_code.is_active),
                "scan_count": scan_count,
            },
        )
