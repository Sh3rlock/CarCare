from django.db import models
from django.urls import reverse

from apps.services.models import ServiceRecord


class Quote(models.Model):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="quotes",
    )
    date = models.DateField()
    title = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    total_estimate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    converted_service = models.ForeignKey(
        "services.ServiceRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_quotes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title or f"Quote #{self.pk} — {self.date}"

    def get_absolute_url(self):
        return reverse("quotes:detail", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})


class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    service_type = models.CharField(max_length=20, choices=ServiceRecord.SERVICE_CHOICES, blank=True)
    replacement_part = models.CharField(max_length=200, blank=True)
    part_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    consumable = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        name = self.get_service_type_catalog_display() or "Quote item"
        return f"{name} ({self.quote.date})"

    def get_service_type_catalog_display(self):
        if not self.service_type:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("service_type", getattr(self.quote.vehicle, "garage", None)):
            if value == self.service_type:
                return label
        return self.get_service_type_display()

    def get_consumable_display(self):
        if not self.consumable:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("consumables", getattr(self.quote.vehicle, "garage", None)):
            if value == self.consumable:
                return label
        return self.consumable
