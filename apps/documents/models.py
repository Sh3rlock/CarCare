import os

from django.db import models
from django.urls import reverse


def document_upload_to(instance, filename):
    return f"documents/vehicle_{instance.vehicle_id}/{os.path.basename(filename)}"


def image_upload_to(instance, filename):
    return f"vehicle_images/vehicle_{instance.vehicle_id}/{os.path.basename(filename)}"


class VehicleDocument(models.Model):
    REGISTRATION = "registration"
    INSURANCE = "insurance"
    SERVICE = "service"
    INSPECTION = "inspection"
    WARRANTY = "warranty"
    PURCHASE = "purchase"
    OTHER = "other"

    DOC_TYPE_CHOICES = [
        (REGISTRATION, "Registration"),
        (INSURANCE, "Insurance"),
        (SERVICE, "Service Record"),
        (INSPECTION, "Inspection Certificate"),
        (WARRANTY, "Warranty"),
        (PURCHASE, "Purchase Agreement"),
        (OTHER, "Other"),
    ]

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default=OTHER)
    file = models.FileField(upload_to=document_upload_to)
    notes = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title

    def get_delete_url(self):
        return reverse("documents:doc-delete", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1].lstrip(".").lower()


class VehicleImage(models.Model):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="images",
    )
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to=image_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title or f"Image {self.pk}"

    def get_delete_url(self):
        return reverse("documents:img-delete", kwargs={"vehicle_pk": self.vehicle_id, "pk": self.pk})
