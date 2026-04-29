from django.db import models
from django.urls import reverse


class MileageLog(models.Model):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="mileage_logs",
    )
    date = models.DateField()
    odometer = models.PositiveIntegerField(help_text="Jelenlegi kilométeróra állás")
    notes = models.CharField(max_length=200, blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} — {self.odometer:,}"

    def get_edit_url(self):
        return reverse("mileage:update", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    def get_delete_url(self):
        return reverse("mileage:delete", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})
