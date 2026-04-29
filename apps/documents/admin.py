from django.contrib import admin

from .models import VehicleDocument, VehicleImage


@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "doc_type", "vehicle", "filename", "uploaded_at")
    list_filter = ("doc_type",)
    search_fields = ("title", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("uploaded_at",)
    raw_id_fields = ("vehicle",)

    def filename(self, obj):
        return obj.filename
    filename.short_description = "File"


@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vehicle", "uploaded_at")
    search_fields = ("title", "vehicle__make", "vehicle__model", "vehicle__owner__username")
    readonly_fields = ("uploaded_at",)
    raw_id_fields = ("vehicle",)
