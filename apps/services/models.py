from django.db import models
from django.urls import reverse


class ServiceRecord(models.Model):
    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    TIRE_REPLACE = "tire_replacement"
    BRAKE_SERVICE = "brake_service"
    BATTERY = "battery"
    AIR_FILTER = "air_filter"
    FUEL_FILTER = "fuel_filter"
    SPARK_PLUGS = "spark_plugs"
    COOLANT = "coolant"
    TRANSMISSION = "transmission"
    INSPECTION = "inspection"
    REPAIR = "repair"
    OTHER = "other"

    SERVICE_CHOICES = [
        (OIL_CHANGE, "Oil Change"),
        (TIRE_ROTATION, "Tire Rotation"),
        (TIRE_REPLACE, "Tire Replacement"),
        (BRAKE_SERVICE, "Brake Service"),
        (BATTERY, "Battery"),
        (AIR_FILTER, "Air Filter"),
        (FUEL_FILTER, "Fuel Filter"),
        (SPARK_PLUGS, "Spark Plugs"),
        (COOLANT, "Coolant Flush"),
        (TRANSMISSION, "Transmission Service"),
        (INSPECTION, "Inspection / MOT"),
        (REPAIR, "Repair"),
        (OTHER, "Other"),
    ]

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="service_records",
    )
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, default=OTHER, blank=True)
    title = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilométeróra állás a szerviz időpontjában (km vagy mérföld)",
    )
    cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="A szerviz teljes költsége",
    )
    workshop = models.CharField(max_length=200, blank=True, help_text="Garázs vagy szerelő neve")
    consumables = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        first_item = self.items.order_by("id").first()
        if first_item:
            return f"{first_item.get_service_type_catalog_display()} — {self.date}"
        if self.service_type:
            return f"{self.get_service_type_catalog_display()} — {self.date}"
        return f"Service — {self.date}"

    def get_service_type_catalog_display(self):
        if not self.service_type:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("service_type", getattr(self.vehicle, "garage", None)):
            if value == self.service_type:
                return label
        return self.get_service_type_display()

    def get_consumables_display(self):
        if not self.consumables:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("consumables", getattr(self.vehicle, "garage", None)):
            if value == self.consumables:
                return label
        return self.consumables

    def get_absolute_url(self):
        return reverse(
            "services:detail",
            kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk},
        )

    def has_repair_item(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {})
        if "items" in prefetched:
            return any(item.service_type == self.REPAIR for item in prefetched["items"])
        return self.items.filter(service_type=self.REPAIR).exists()


class ServiceRecordItem(models.Model):
    record = models.ForeignKey(ServiceRecord, on_delete=models.CASCADE, related_name="items")
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
        name = self.get_service_type_catalog_display() or "Service item"
        return f"{name} ({self.record.date})"

    def get_service_type_catalog_display(self):
        if not self.service_type:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("service_type", getattr(self.record.vehicle, "garage", None)):
            if value == self.service_type:
                return label
        return self.get_service_type_display()

    def get_consumable_display(self):
        if not self.consumable:
            return ""
        from apps.catalog.utils import get_dropdown_choices

        for value, label in get_dropdown_choices("consumables", getattr(self.record.vehicle, "garage", None)):
            if value == self.consumable:
                return label
        return self.consumable
