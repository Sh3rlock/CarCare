from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import VehicleDocument, VehicleImage


@receiver(post_delete, sender=VehicleDocument)
def delete_document_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)


@receiver(post_delete, sender=VehicleImage)
def delete_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
