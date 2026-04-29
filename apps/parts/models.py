import datetime

from django.db import models
from django.urls import reverse


class PartReplacement(models.Model):
    OIL_FILTER = "oil_filter"
    AIR_FILTER = "air_filter"
    FUEL_FILTER = "fuel_filter"
    CABIN_FILTER = "cabin_filter"
    BRAKE_PADS_F = "brake_pads_front"
    BRAKE_PADS_R = "brake_pads_rear"
    BRAKE_DISCS_F = "brake_discs_front"
    BRAKE_DISCS_R = "brake_discs_rear"
    TIMING_BELT = "timing_belt"
    TIMING_CHAIN = "timing_chain"
    SERPENTINE = "serpentine_belt"
    SPARK_PLUGS = "spark_plugs"
    GLOW_PLUGS = "glow_plugs"
    BATTERY = "battery"
    TYRE_FL = "tyre_fl"
    TYRE_FR = "tyre_fr"
    TYRE_RL = "tyre_rl"
    TYRE_RR = "tyre_rr"
    WIPER_BLADES = "wiper_blades"
    COOLANT = "coolant"
    BRAKE_FLUID = "brake_fluid"
    TRANS_FLUID = "transmission_fluid"
    OTHER = "other"

    PART_CHOICES = [
        ("Filters", [
            (OIL_FILTER, "Oil Filter"),
            (AIR_FILTER, "Air Filter"),
            (FUEL_FILTER, "Fuel Filter"),
            (CABIN_FILTER, "Cabin Air Filter"),
        ]),
        ("Brakes", [
            (BRAKE_PADS_F, "Brake Pads (Front)"),
            (BRAKE_PADS_R, "Brake Pads (Rear)"),
            (BRAKE_DISCS_F, "Brake Discs (Front)"),
            (BRAKE_DISCS_R, "Brake Discs (Rear)"),
        ]),
        ("Belts & Ignition", [
            (TIMING_BELT, "Timing Belt"),
            (TIMING_CHAIN, "Timing Chain"),
            (SERPENTINE, "Serpentine Belt"),
            (SPARK_PLUGS, "Spark Plugs"),
            (GLOW_PLUGS, "Glow Plugs"),
        ]),
        ("Tyres & Electrical", [
            (BATTERY, "Battery"),
            (TYRE_FL, "Tyre (Front Left)"),
            (TYRE_FR, "Tyre (Front Right)"),
            (TYRE_RL, "Tyre (Rear Left)"),
            (TYRE_RR, "Tyre (Rear Right)"),
            (WIPER_BLADES, "Wiper Blades"),
        ]),
        ("Fluids", [
            (COOLANT, "Coolant"),
            (BRAKE_FLUID, "Brake Fluid"),
            (TRANS_FLUID, "Transmission Fluid"),
        ]),
        ("Other", [
            (OTHER, "Other"),
        ]),
    ]

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="part_replacements",
    )
    part_type = models.CharField(max_length=30, choices=PART_CHOICES, default=OTHER)
    part_name = models.CharField(max_length=200, help_text="Konkrét alkatrésznév vagy leírás")
    part_number = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    mileage_at_replacement = models.PositiveIntegerField(null=True, blank=True)
    next_replacement_mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilométeróra állás a következő csere esedékességekor",
    )
    next_replacement_date = models.DateField(
        null=True,
        blank=True,
        help_text="A következő csere esedékességének dátuma",
    )
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    workshop = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_part_type_display()} — {self.date}"

    def get_absolute_url(self):
        return reverse("parts:detail", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    @property
    def is_overdue(self):
        if self.next_replacement_date:
            return self.next_replacement_date < datetime.date.today()
        return False
