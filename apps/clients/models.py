from django.conf import settings
from django.db import models
from django.urls import reverse


class Client(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    garage = models.ForeignKey(
        "garages.Garage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        verbose_name="Garázs",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=200, blank=True, verbose_name="Cég / szervezet")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        name = " ".join(p for p in [self.first_name, self.last_name] if p).strip()
        if self.company:
            return f"{name} ({self.company})" if name else self.company
        return name or "—"

    @property
    def full_name(self):
        return " ".join(p for p in [self.last_name, self.first_name] if p).strip()

    def get_absolute_url(self):
        return reverse("clients:detail", kwargs={"pk": self.pk})
