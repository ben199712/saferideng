from django.contrib import admin

from .models import EmergencyAlert, EmergencyContact, SOSAlertDeliveryLog, SOSAuthorityAccessLog, SOSAuthorityContact


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "relationship", "user", "created_at")
    list_filter = ("relationship", "created_at")
    search_fields = ("full_name", "phone_number", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ("uuid", "trip", "alert_type", "status", "triggered_by", "created_at", "resolved_at")
    list_filter = ("alert_type", "status")
    search_fields = ("uuid", "trip__passenger_name", "trip__passenger_phone", "trip__driver__email")
    readonly_fields = ("uuid", "created_at", "resolved_at", "details_snapshot")


@admin.register(SOSAuthorityContact)
class SOSAuthorityContactAdmin(admin.ModelAdmin):
    list_display = ("authority_name", "physical_jurisdiction", "official_email", "sms_phone_number", "is_active", "updated_at")
    list_filter = ("is_active", "physical_jurisdiction")
    search_fields = ("authority_name", "physical_jurisdiction", "official_email", "sms_phone_number")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SOSAlertDeliveryLog)
class SOSAlertDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("alert", "recipient_type", "channel", "destination", "status", "created_at", "delivered_at")
    list_filter = ("recipient_type", "channel", "status")
    search_fields = ("destination", "provider_reference", "alert__uuid")
    readonly_fields = ("created_at",)


@admin.register(SOSAuthorityAccessLog)
class SOSAuthorityAccessLogAdmin(admin.ModelAdmin):
    list_display = ("admin_user", "action", "authority_contact", "request_path", "ip_address", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("admin_user__email", "request_path", "authority_contact__authority_name")
    readonly_fields = ("created_at",)
