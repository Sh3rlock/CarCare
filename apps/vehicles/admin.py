from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "fuel_type", "transmission", "created_at")
    list_filter = ("fuel_type", "transmission")
    search_fields = ("make", "model", "license_plate", "vin", "owner__username")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner",)
