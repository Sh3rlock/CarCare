from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("title", "vehicle", "due_date", "due_mileage", "is_done")
    list_filter = ("is_done",)
    search_fields = ("title", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("created_at",)
    raw_id_fields = ("vehicle",)
