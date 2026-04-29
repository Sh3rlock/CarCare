from django.db import models

FORM_CHOICES = [
    ("vehicle", "Vehicle"),
    ("client", "Client"),
    ("service", "Service Record"),
    ("quote", "Quote"),
    ("part", "Part Replacement"),
    ("mileage", "Mileage Log"),
    ("insurance", "Insurance Policy"),
    ("reminder", "Reminder"),
]

FIELD_TYPE_CHOICES = [
    ("text", "Short Text"),
    ("textarea", "Long Text"),
    ("number", "Number"),
    ("decimal", "Decimal"),
    ("date", "Date"),
]

MODULE_CHOICES = [
    ("services", "Service Records"),
    ("quotes", "Quotes"),
    ("parts", "Part Replacements"),
    ("mileage", "Mileage Log"),
    ("insurance", "Insurance Policy"),
    ("documents", "Documents & Images"),
    ("reminders", "Reminders"),
]

_GARAGE_FK = dict(
    to="garages.Garage",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
)


class BuiltinFieldConfig(models.Model):
    """Controls visibility and label of built-in form fields."""

    garage = models.ForeignKey(**_GARAGE_FK, related_name="builtin_field_configs")
    form_key = models.CharField(max_length=20, choices=FORM_CHOICES)
    field_name = models.CharField(max_length=100)
    label_override = models.CharField(max_length=200, blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        # NULL garage = global config. PostgreSQL treats NULLs as distinct in
        # unique constraints, so app-layer must use get_or_create(garage=None,…)
        # to prevent global duplicates.
        unique_together = [("garage", "form_key", "field_name")]
        ordering = ["form_key", "field_name"]

    def __str__(self):
        return f"{self.form_key}.{self.field_name}"


class CustomField(models.Model):
    """Defines admin-created extra fields appended to a built-in form."""

    garage = models.ForeignKey(**_GARAGE_FK, related_name="custom_fields")
    form_key = models.CharField(max_length=20, choices=FORM_CHOICES)
    label = models.CharField(max_length=200)
    field_key = models.SlugField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default="text")
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [("garage", "form_key", "field_key")]
        ordering = ["form_key", "position", "label"]

    def __str__(self):
        return f"{self.get_form_key_display()}: {self.label}"

    def save(self, *args, **kwargs):
        if not self.field_key:
            from django.utils.text import slugify
            base = slugify(self.label)[:90] or "field"
            slug = base
            n = 1
            while CustomField.objects.filter(
                garage=self.garage, form_key=self.form_key, field_key=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.field_key = slug
        super().save(*args, **kwargs)


class ModuleConfig(models.Model):
    """Controls whether a built-in module (mileage, insurance, …) is enabled."""

    garage = models.ForeignKey(**_GARAGE_FK, related_name="module_configs")
    module_key = models.CharField(max_length=30, choices=MODULE_CHOICES)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = [("garage", "module_key")]
        ordering = ["module_key"]

    def __str__(self):
        state = "enabled" if self.is_enabled else "disabled"
        return f"{self.get_module_key_display()} ({state})"


class DynamicModule(models.Model):
    """An admin-created section (e.g. 'Client Data') that appears on every vehicle."""

    garage = models.ForeignKey(**_GARAGE_FK, related_name="dynamic_modules")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    is_enabled = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [("garage", "slug")]
        ordering = ["position", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name)[:90] or "module"
            slug = base
            n = 1
            while DynamicModule.objects.filter(
                garage=self.garage, slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DynamicModuleField(models.Model):
    """A field definition belonging to a DynamicModule."""

    module = models.ForeignKey(DynamicModule, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=200)
    field_key = models.SlugField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default="text")
    is_required = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [("module", "field_key")]
        ordering = ["position", "label"]

    def __str__(self):
        return f"{self.module.name}: {self.label}"

    def save(self, *args, **kwargs):
        if not self.field_key:
            from django.utils.text import slugify
            base = slugify(self.label)[:90] or "field"
            slug = base
            n = 1
            while DynamicModuleField.objects.filter(
                module=self.module, field_key=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.field_key = slug
        super().save(*args, **kwargs)
