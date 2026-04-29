from django.db import models
from django.urls import reverse


class DynamicRecord(models.Model):
    """Stores one record entry for a DynamicModule on a vehicle."""

    module = models.ForeignKey(
        "formconfig.DynamicModule",
        on_delete=models.CASCADE,
        related_name="records",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="dynamic_records",
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.module.name} — {self.created_at.date()}"

    def get_absolute_url(self):
        return reverse(
            "dynamic:list",
            kwargs={"vehicle_pk": self.vehicle_id, "module_slug": self.module.slug},
        )
