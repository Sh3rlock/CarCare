from django.contrib import admin

from .models import MileageLog


@admin.register(MileageLog)
class MileageLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "date", "odometer", "notes")
    search_fields = ("vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "date"
    raw_id_fields = ("vehicle",)
