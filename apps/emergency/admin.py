from django.contrib import admin

from .models import EmergencyAlert, EmergencyContact


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
    readonly_fields = ("uuid", "created_at", "resolved_at")
