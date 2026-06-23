from django.contrib import admin

from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "verification_status",
        "is_approved",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_filter = ("verification_status", "is_approved")

