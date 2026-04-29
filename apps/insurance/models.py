import datetime

from django.db import models
from django.urls import reverse


class InsurancePolicy(models.Model):
    THIRD_PARTY = "third_party"
    TPFT = "third_party_fire_theft"
    COMPREHENSIVE = "comprehensive"
    OTHER = "other"

    COVERAGE_CHOICES = [
        (THIRD_PARTY, "Third Party"),
        (TPFT, "Third Party, Fire & Theft"),
        (COMPREHENSIVE, "Comprehensive"),
        (OTHER, "Other"),
    ]

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"

    PERIOD_CHOICES = [
        (MONTHLY, "Monthly"),
        (QUARTERLY, "Quarterly"),
        (SEMI_ANNUAL, "Semi-Annual"),
        (ANNUAL, "Annual"),
    ]

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="insurance_policies",
    )
    provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    coverage_type = models.CharField(
        max_length=30, choices=COVERAGE_CHOICES, default=COMPREHENSIVE
    )
    start_date = models.DateField()
    end_date = models.DateField()
    premium = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    premium_period = models.CharField(
        max_length=15, choices=PERIOD_CHOICES, default=ANNUAL, blank=True
    )
    agent_name = models.CharField(max_length=200, blank=True)
    agent_phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["end_date"]
        verbose_name = "Biztosítási kötvény"
        verbose_name_plural = "Biztosítási kötvények"

    def __str__(self):
        return f"{self.provider} ({self.policy_number})"

    def get_absolute_url(self):
        return reverse(
            "insurance:detail",
            kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk},
        )

    @property
    def is_active(self):
        today = datetime.date.today()
        return self.start_date <= today <= self.end_date

    @property
    def is_expired(self):
        return self.end_date < datetime.date.today()

    @property
    def is_expiring_soon(self):
        today = datetime.date.today()
        return today <= self.end_date <= today + datetime.timedelta(days=30)

    @property
    def days_until_expiry(self):
        delta = self.end_date - datetime.date.today()
        return delta.days
