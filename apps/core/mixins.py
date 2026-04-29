import datetime

from django import forms as django_forms
from django.shortcuts import get_object_or_404

from apps.vehicles.models import Vehicle


class VehicleOwnerMixin:
    """
    Single source of truth for vehicle ownership verification.

    Fetches the parent Vehicle by `vehicle_pk` URL kwarg, filtered to
    request.user. Returns 404 (not 403) to avoid leaking whether a resource
    exists. Result is cached on the instance so the DB is hit once per
    request even when multiple methods call get_vehicle().

    Subclasses that need queryset filtering must override get_queryset().
    """

    def get_vehicle(self):
        if not hasattr(self, "_vehicle"):
            self._vehicle = get_object_or_404(
                Vehicle,
                pk=self.kwargs["vehicle_pk"],
                owner=self.request.user,
            )
        return self._vehicle

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vehicle"] = self.get_vehicle()
        return context


class ConfigurableFormMixin:
    """
    ModelForm mixin that reads BuiltinFieldConfig and CustomField to
    dynamically hide/relabel built-in fields and inject custom fields.

    Subclass must set:  form_key = 'vehicle'  (matching formconfig.utils keys)
    """

    form_key = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.form_key:
            return

        from apps.formconfig.utils import get_custom_fields, get_hidden_fields, get_label_overrides

        # --- built-in field configuration ---
        hidden = get_hidden_fields(self.form_key)
        self.hidden_field_names = hidden
        for name in list(hidden):
            if name in self.fields:
                del self.fields[name]

        for name, label in get_label_overrides(self.form_key).items():
            if name in self.fields:
                self.fields[name].label = label

        # --- custom fields ---
        custom_fields = list(get_custom_fields(self.form_key))
        self.custom_field_instances = custom_fields

        existing = {}
        if hasattr(self, "instance") and self.instance and self.instance.pk:
            existing = getattr(self.instance, "custom_data", None) or {}

        for cf in custom_fields:
            self.fields[cf.field_key] = self._make_custom_field(cf)
            if cf.field_key in existing:
                self.initial[cf.field_key] = existing[cf.field_key]

    def _make_custom_field(self, cf):
        base = {"required": cf.is_required, "label": cf.label}
        if cf.field_type == "textarea":
            return django_forms.CharField(
                widget=django_forms.Textarea(attrs={"class": "form-control", "rows": 3}),
                **base,
            )
        if cf.field_type == "number":
            return django_forms.IntegerField(
                widget=django_forms.NumberInput(attrs={"class": "form-control"}),
                **base,
            )
        if cf.field_type == "decimal":
            return django_forms.DecimalField(
                widget=django_forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
                **base,
            )
        if cf.field_type == "date":
            return django_forms.DateField(
                widget=django_forms.DateInput(attrs={"class": "form-control", "type": "date"}),
                **base,
            )
        # default: text
        return django_forms.CharField(
            widget=django_forms.TextInput(attrs={"class": "form-control"}),
            **base,
        )

    def custom_bound_fields(self):
        """Returns BoundFields for each visible custom field (called from templates)."""
        return [
            self[cf.field_key]
            for cf in getattr(self, "custom_field_instances", [])
            if cf.field_key in self.fields
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.form_key and hasattr(instance, "custom_data"):
            custom_data = {}
            for cf in getattr(self, "custom_field_instances", []):
                if cf.field_key in self.cleaned_data:
                    val = self.cleaned_data[cf.field_key]
                    if val is None or val == "":
                        custom_data[cf.field_key] = ""
                    elif isinstance(val, datetime.date):
                        custom_data[cf.field_key] = val.isoformat()
                    else:
                        custom_data[cf.field_key] = str(val)
            instance.custom_data = custom_data
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ModuleEnabledMixin:
    """
    View mixin: raises Http404 when the module this view belongs to is disabled.
    Subclasses must set:  module_key = 'mileage'  (matching MODULE_LABELS keys)
    """

    module_key = None

    def dispatch(self, request, *args, **kwargs):
        if self.module_key:
            from apps.formconfig.models import ModuleConfig
            config = ModuleConfig.objects.filter(module_key=self.module_key, garage__isnull=True).first()
            if config is not None and not config.is_enabled:
                from django.http import Http404
                raise Http404("This module is disabled.")
        return super().dispatch(request, *args, **kwargs)


class FormConfigContextMixin:
    """View mixin: injects hidden_fields into template context for ConfigurableFormMixin forms."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        context["hidden_fields"] = getattr(form, "hidden_field_names", set())
        return context
