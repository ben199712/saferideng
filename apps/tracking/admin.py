from django.contrib import admin
from .models import TripShare, LocationUpdate


@admin.register(TripShare)
class TripShareAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'sharer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['trip__id', 'sharer__email']


@admin.register(LocationUpdate)
class LocationUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip_share', 'timestamp', 'latitude', 'longitude']
    list_filter = ['timestamp']
    readonly_fields = ['timestamp']
