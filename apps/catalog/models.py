from django.db import models

_GARAGE_FK = dict(to="garages.Garage", on_delete=models.CASCADE, null=True, blank=True)


class CarMake(models.Model):
    garage = models.ForeignKey(**_GARAGE_FK, related_name="catalog_makes")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        unique_together = [("garage", "name")]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    garage = models.ForeignKey(**_GARAGE_FK, related_name="catalog_models")
    make = models.ForeignKey(CarMake, on_delete=models.CASCADE, related_name="car_models")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        unique_together = [("garage", "make", "name")]

    def __str__(self):
        return self.name


DROPDOWN_LIST_CHOICES = [
    ("fuel_type", "Fuel Type"),
    ("transmission", "Transmission"),
    ("service_type", "Service Type"),
    ("consumables", "Consumables"),
]


class DropdownChoice(models.Model):
    garage = models.ForeignKey(**_GARAGE_FK, related_name="catalog_dropdown_choices")
    list_key = models.CharField(max_length=50, choices=DROPDOWN_LIST_CHOICES)
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["list_key", "position", "label"]
        unique_together = [("garage", "list_key", "value")]

    def __str__(self):
        return f"{self.get_list_key_display()}: {self.label}"
