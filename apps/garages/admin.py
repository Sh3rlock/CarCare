from django.contrib import admin

from .models import Garage, GarageMembership


class GarageMembershipInline(admin.TabularInline):
    model = GarageMembership
    extra = 1
    fields = ("user", "role", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "is_active", "member_count", "vehicle_count", "created_at")
    search_fields = ("name", "slug", "owner__username", "owner__email")
    list_filter = ("is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [GarageMembershipInline]
    raw_id_fields = ("owner",)
    actions = ["activate_garages", "deactivate_garages"]

    @admin.action(description="Activate selected garages")
    def activate_garages(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected garages")
    def deactivate_garages(self, request, queryset):
        queryset.update(is_active=False)

    @admin.display(description="Members")
    def member_count(self, obj):
        return obj.memberships.count()

    @admin.display(description="Vehicles")
    def vehicle_count(self, obj):
        return obj.vehicles.count()


@admin.register(GarageMembership)
class GarageMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "garage", "role", "created_at")
    search_fields = ("user__username", "user__email", "garage__name")
    list_filter = ("role", "garage")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user", "garage")
