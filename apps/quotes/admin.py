from django.contrib import admin

from .models import Quote, QuoteItem


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vehicle", "date", "total_estimate")
    list_filter = ("date",)
    search_fields = ("title", "notes", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    inlines = (QuoteItemInline,)


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ("quote", "service_type", "replacement_part", "part_price", "consumable", "work_hours")
    list_filter = ("service_type", "consumable")
    search_fields = ("replacement_part", "note", "quote__vehicle__make", "quote__vehicle__model")
