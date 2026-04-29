from django.contrib import admin

from .models import ServiceRecord, ServiceRecordItem


class ServiceRecordItemInline(admin.TabularInline):
    model = ServiceRecordItem
    extra = 0


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vehicle", "mileage", "cost", "date")
    list_filter = ("date",)
    search_fields = (
        "vehicle__make",
        "vehicle__model",
        "vehicle__owner__username",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    raw_id_fields = ("vehicle",)
    inlines = (ServiceRecordItemInline,)


@admin.register(ServiceRecordItem)
class ServiceRecordItemAdmin(admin.ModelAdmin):
    list_display = ("record", "service_type", "replacement_part", "part_price", "consumable", "work_hours")
    list_filter = ("service_type", "consumable")
    search_fields = ("replacement_part", "note", "record__vehicle__make", "record__vehicle__model")
