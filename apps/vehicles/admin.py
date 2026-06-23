from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import QRScanLog, Vehicle, VehicleQRCode
from .services import generate_qr_code


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate_number",
        "driver",
        "vehicle_type",
        "registered_route",
        "verification_status",
        "is_active",
        "created_at",
    )
    list_filter = ("vehicle_type", "verification_status", "is_active")
    search_fields = ("plate_number", "driver__email", "driver__first_name", "driver__last_name")
    readonly_fields = ("uuid", "approved_at", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            old_status = (
                Vehicle.objects.filter(pk=obj.pk)
                .values_list("verification_status", flat=True)
                .first()
            )

        if obj.verification_status == Vehicle.VerificationStatus.approved:
            obj.is_active = True
            if obj.approved_at is None:
                obj.approved_at = timezone.now()
        elif obj.verification_status == Vehicle.VerificationStatus.rejected:
            obj.is_active = False
            obj.approved_at = None

        super().save_model(request, obj, form, change)

        qr_code = VehicleQRCode.objects.filter(vehicle=obj).first()
        should_generate_qr = (
            obj.verification_status == Vehicle.VerificationStatus.approved
            and (not change or old_status != Vehicle.VerificationStatus.approved or not qr_code or not qr_code.qr_image)
        )

        if should_generate_qr:
            with transaction.atomic():
                target_url = request.build_absolute_uri(
                    reverse(
                        "driver_public_profile",
                        kwargs={"driver_uuid": obj.driver.uuid, "vehicle_uuid": obj.uuid},
                    )
                )
                generate_qr_code(obj, target_url)


@admin.register(VehicleQRCode)
class VehicleQRCodeAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "token", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("vehicle__plate_number", "token")
    readonly_fields = ("token", "created_at")


@admin.register(QRScanLog)
class QRScanLogAdmin(admin.ModelAdmin):
    list_display = ("qr_code", "ip_address", "scanned_at")
    search_fields = ("qr_code__vehicle__plate_number", "ip_address")
    list_filter = ("scanned_at",)
    readonly_fields = ("scanned_at",)
