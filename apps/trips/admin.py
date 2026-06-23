from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "passenger_name",
        "passenger_phone",
        "driver",
        "vehicle",
        "trip_status",
        "started_at",
        "ended_at",
        "created_at",
    )
    list_filter = ("trip_status",)
    search_fields = (
        "passenger_name",
        "passenger_phone",
        "destination",
        "driver__email",
        "vehicle__plate_number",
    )
    readonly_fields = ("uuid", "started_at", "created_at")
