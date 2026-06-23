from django.contrib import admin

from .models import IncidentReport


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ("uuid", "trip", "report_type", "status", "created_at")
    list_filter = ("report_type", "status")
    search_fields = ("uuid", "description", "trip__passenger_name", "trip__driver__email")
    readonly_fields = ("uuid", "created_at")
