from django.contrib import admin

from .models import PartReplacement


@admin.register(PartReplacement)
class PartReplacementAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vehicle", "part_name", "brand", "cost", "next_replacement_date")
    list_filter = ("part_type",)
    search_fields = ("part_name", "brand", "part_number", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    raw_id_fields = ("vehicle",)
