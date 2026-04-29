from django.contrib import admin

from .models import InsurancePolicy


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vehicle", "coverage_type", "start_date", "end_date", "premium")
    list_filter = ("coverage_type", "premium_period")
    search_fields = ("provider", "policy_number", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "end_date"
    raw_id_fields = ("vehicle",)
