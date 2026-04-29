from django.conf import settings
from django.db import models
from django.urls import reverse


class Vehicle(models.Model):
    FUEL_PETROL = "petrol"
    FUEL_DIESEL = "diesel"
    FUEL_ELECTRIC = "electric"
    FUEL_HYBRID = "hybrid"
    FUEL_LPG = "lpg"
    FUEL_OTHER = "other"
    FUEL_CHOICES = [
        (FUEL_PETROL, "Petrol"),
        (FUEL_DIESEL, "Diesel"),
        (FUEL_ELECTRIC, "Electric"),
        (FUEL_HYBRID, "Hybrid"),
        (FUEL_LPG, "LPG"),
        (FUEL_OTHER, "Other"),
    ]

    TRANS_MANUAL = "manual"
    TRANS_AUTO = "automatic"
    TRANS_SEMI = "semi_auto"
    TRANSMISSION_CHOICES = [
        (TRANS_MANUAL, "Manual"),
        (TRANS_AUTO, "Automatic"),
        (TRANS_SEMI, "Semi-Automatic"),
    ]

    DOORS_CHOICES = [(2, "2"), (3, "3"), (4, "4"), (5, "5")]

    AC_YES = "yes"
    AC_NO = "no"
    AC_CHOICES = [(AC_YES, "Yes"), (AC_NO, "No")]

    DRIVE_FWD = "fwd"
    DRIVE_RWD = "rwd"
    DRIVE_4X4 = "4x4"
    DRIVE_AWD = "awd"
    DRIVE_CHOICES = [
        (DRIVE_FWD, "Front-Wheel Drive (FWD)"),
        (DRIVE_RWD, "Rear-Wheel Drive (RWD)"),
        (DRIVE_4X4, "4x4"),
        (DRIVE_AWD, "All-Wheel Drive (AWD)"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
        verbose_name="Ügyfél",
    )
    garage = models.ForeignKey(
        "garages.Garage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
        verbose_name="Garázs",
    )
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    license_plate = models.CharField(max_length=20)
    vin = models.CharField(
        max_length=17,
        blank=True,
        verbose_name="VIN",
        help_text="17 karakteres járműazonosító szám",
    )
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES, default=FUEL_PETROL)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES, default=TRANS_MANUAL)
    color = models.CharField(max_length=50, blank=True)
    ccm = models.PositiveIntegerField(blank=True, null=True, verbose_name="Motor (ccm)")
    hp = models.PositiveIntegerField(blank=True, null=True, verbose_name="Teljesítmény (LE)")
    engine_code = models.CharField(max_length=50, blank=True, verbose_name="Motorkód")
    doors = models.PositiveSmallIntegerField(blank=True, null=True, choices=DOORS_CHOICES, verbose_name="Ajtók")
    has_ac = models.CharField(max_length=3, blank=True, choices=AC_CHOICES, verbose_name="Klíma")
    drive_type = models.CharField(max_length=10, blank=True, choices=DRIVE_CHOICES, verbose_name="Hajtás típusa")
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} · {self.license_plate}"

    def get_absolute_url(self):
        return reverse("vehicles:detail", kwargs={"pk": self.pk})
