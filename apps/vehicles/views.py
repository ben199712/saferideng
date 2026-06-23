from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from accounts.models import User

from .forms import VehicleRegistrationForm
from .models import Vehicle, VehicleQRCode
from .services import generate_qr_code
from .utils import create_scan_log


def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.role in (User.Roles.super_admin, User.Roles.admin)
    )


class DriverRequiredMixin:
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != User.Roles.driver:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DriverVehicleListView(DriverRequiredMixin, View):
    template_name = "vehicles/driver_vehicle_list.html"

    def get(self, request, *args, **kwargs):
        vehicles = (
            Vehicle.objects.filter(driver=request.user)
            .select_related("qr_code")
            .order_by("-created_at")
        )
        return render(request, self.template_name, {"vehicles": vehicles})


class DriverVehicleCreateView(DriverRequiredMixin, View):
    template_name = "vehicles/driver_vehicle_form.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form": VehicleRegistrationForm()})

    def post(self, request, *args, **kwargs):
        form = VehicleRegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        vehicle = form.save(commit=False)
        vehicle.driver = request.user
        vehicle.save()
        messages.success(request, "Vehicle registered and submitted for approval.")
        return redirect("driver_vehicle_list")


class DriverVehicleUpdateView(DriverRequiredMixin, View):
    template_name = "vehicles/driver_vehicle_form.html"

    def get_vehicle(self, request, uuid):
        return get_object_or_404(Vehicle.objects.filter(driver=request.user), uuid=uuid)

    def get(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(request, uuid)
        return render(
            request,
            self.template_name,
            {"form": VehicleRegistrationForm(instance=vehicle), "vehicle": vehicle},
        )

    def post(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(request, uuid)
        form = VehicleRegistrationForm(request.POST, instance=vehicle)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "vehicle": vehicle})

        form.save()
        vehicle.mark_pending()
        try:
            qr_code = vehicle.qr_code
        except VehicleQRCode.DoesNotExist:
            qr_code = None
        if qr_code is not None:
            qr_code.is_active = False
            qr_code.save(update_fields=["is_active"])
        messages.success(request, "Vehicle updated and resubmitted for approval.")
        return redirect("driver_vehicle_list")


class DriverVehicleDownloadView(DriverRequiredMixin, View):
    def get_vehicle(self, request, uuid):
        return get_object_or_404(Vehicle.objects.filter(driver=request.user), uuid=uuid)

    def get(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(request, uuid)
        try:
            qr_code = vehicle.qr_code
        except VehicleQRCode.DoesNotExist:
            messages.error(request, "QR code is not available for this vehicle yet.")
            return redirect("driver_vehicle_list")

        if not qr_code.qr_image:
            messages.error(request, "QR code image is not available yet.")
            return redirect("driver_vehicle_list")

        return FileResponse(
            qr_code.qr_image.open("rb"),
            as_attachment=True,
            filename=f"{vehicle.plate_number}-qr.png",
        )


class VehicleVerificationView(View):
    template_name = "vehicles/public_vehicle_verification.html"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_state(self, vehicle):
        if vehicle.verification_status == Vehicle.VerificationStatus.rejected:
            return "rejected"
        if not vehicle.is_active:
            return "suspended"
        if vehicle.verification_status == Vehicle.VerificationStatus.approved:
            return "verified"
        return "pending"

    def get(self, request, token, *args, **kwargs):
        qr_code = (
            VehicleQRCode.objects.select_related("vehicle__driver")
            .filter(token=token, is_active=True)
            .first()
        )

        if qr_code is None:
            return render(request, self.template_name, {"state": "invalid"})

        create_scan_log(qr_code, request)
        vehicle = qr_code.vehicle
        return redirect(
            "driver_public_profile",
            driver_uuid=vehicle.driver.uuid,
            vehicle_uuid=vehicle.uuid,
        )


class AdminVehicleDashboardView(AdminRequiredMixin, View):
    template_name = "vehicles/admin_vehicle_dashboard.html"

    def get(self, request, *args, **kwargs):
        vehicles = (
            Vehicle.objects.select_related("driver", "qr_code")
            .annotate(scan_count=Count("qr_code__scan_logs"))
            .order_by("-created_at")
        )
        stats = {
            "total": vehicles.count(),
            "pending": vehicles.filter(verification_status=Vehicle.VerificationStatus.pending).count(),
            "approved": vehicles.filter(verification_status=Vehicle.VerificationStatus.approved).count(),
            "rejected": vehicles.filter(verification_status=Vehicle.VerificationStatus.rejected).count(),
        }
        return render(
            request,
            self.template_name,
            {"vehicles": vehicles, "stats": stats},
        )


class AdminVehicleDetailView(AdminRequiredMixin, View):
    template_name = "vehicles/admin_vehicle_detail.html"

    def get_vehicle(self, uuid):
        return get_object_or_404(Vehicle.objects.select_related("driver"), uuid=uuid)

    def get_qr_code(self, vehicle):
        return VehicleQRCode.objects.filter(vehicle=vehicle).first()

    def get(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(uuid)
        qr_code = self.get_qr_code(vehicle)
        return render(
            request,
            self.template_name,
            {
                "vehicle": vehicle,
                "qr_code": qr_code,
                "scan_count": qr_code.scan_logs.count() if qr_code else 0,
            },
        )


class AdminVehicleActionView(AdminRequiredMixin, View):
    def get_vehicle(self, uuid):
        return get_object_or_404(Vehicle.objects.select_related("driver"), uuid=uuid)

    def post(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(uuid)
        action = request.POST.get("action")

        if action == "approve":
            with transaction.atomic():
                vehicle.approve()
                profile_url = request.build_absolute_uri(
                    reverse(
                        "driver_public_profile",
                        kwargs={"driver_uuid": vehicle.driver.uuid, "vehicle_uuid": vehicle.uuid},
                    )
                )
                generate_qr_code(vehicle, profile_url)
            messages.success(request, "Vehicle approved and QR code generated.")
        elif action == "reject":
            vehicle.reject()
            messages.success(request, "Vehicle rejected.")
        else:
            raise Http404

        return redirect("admin_vehicle_detail", uuid=vehicle.uuid)


class AdminVehicleDownloadView(AdminRequiredMixin, View):
    def get_vehicle(self, uuid):
        return get_object_or_404(Vehicle.objects.select_related("driver"), uuid=uuid)

    def get(self, request, uuid, *args, **kwargs):
        vehicle = self.get_vehicle(uuid)
        try:
            qr_code = vehicle.qr_code
        except VehicleQRCode.DoesNotExist:
            messages.error(request, "QR code is not available for this vehicle yet.")
            return redirect("admin_vehicle_detail", uuid=vehicle.uuid)

        if not qr_code.qr_image:
            messages.error(request, "QR code image is not available yet.")
            return redirect("admin_vehicle_detail", uuid=vehicle.uuid)

        return FileResponse(
            qr_code.qr_image.open("rb"),
            as_attachment=True,
            filename=f"{vehicle.plate_number}-qr.png",
        )
