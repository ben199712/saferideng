from django.contrib import admin

from .models import DriverDocument, DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "email",
        "state",
        "transport_union",
        "driver_license_expiry_date",
        "license_expiry_warning",
        "verification_status",
        "is_approved",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__email", "user__first_name", "user__last_name", "email", "state")
    list_filter = ("verification_status", "is_approved", "state", "transport_union", "nationality")
    readonly_fields = ("created_at", "updated_at", "email_verified")

    def license_expiry_warning(self, obj):
        return "Expiring Soon" if obj.is_license_expiring_soon else "OK"

    license_expiry_warning.short_description = "License Alert"


@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "document_type",
        "original_file_name",
        "mime_type",
        "file_size",
        "malware_scan_status",
        "uploaded_at",
    )
    list_filter = ("document_type", "malware_scan_status", "preview_kind")
    search_fields = ("user__email", "user__first_name", "user__last_name", "original_file_name", "checksum_sha256")
    readonly_fields = (
        "uploaded_at",
        "updated_at",
        "checksum_sha256",
        "backup_file_name",
        "file_size",
        "mime_type",
        "preview_kind",
        "malware_scan_status",
        "malware_scan_message",
    )

