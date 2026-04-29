import datetime

from django.db import models
from django.urls import reverse


class Reminder(models.Model):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    due_mileage = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # False (0) sorts before True (1) → active before done.
        # Ascending due_date → overdue (past) first, then soonest upcoming.
        # NULLs sort last in PostgreSQL ASC → undated reminders after dated ones.
        ordering = ["is_done", "due_date"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("reminders:list", kwargs={"vehicle_pk": self.vehicle_id})

    def get_edit_url(self):
        return reverse("reminders:update", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    def get_delete_url(self):
        return reverse("reminders:delete", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    def get_toggle_url(self):
        return reverse("reminders:toggle", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    @property
    def is_overdue(self):
        if self.is_done or not self.due_date:
            return False
        return self.due_date < datetime.date.today()

    @property
    def is_due_soon(self):
        if self.is_done or not self.due_date or self.is_overdue:
            return False
        return self.due_date <= datetime.date.today() + datetime.timedelta(days=30)

    @property
    def days_until_due(self):
        if self.due_date:
            return (self.due_date - datetime.date.today()).days
        return None
