from django.contrib import admin

from .models import EmailNotificationLog


@admin.register(EmailNotificationLog)
class EmailNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "to_email", "status", "provider", "created_at")
    list_filter = ("status", "event_type", "provider")
    search_fields = ("to_email", "subject", "provider_message_id", "error_message")
    readonly_fields = ("created_at",)
