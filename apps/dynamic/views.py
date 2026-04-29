import datetime

from django import forms as django_forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.formconfig.models import DynamicModule
from apps.vehicles.models import Vehicle

from .models import DynamicRecord


class DynamicModuleMixin:
    """Shared logic: fetch vehicle (ownership) and module (slug + enabled)."""

    def _get_vehicle(self, request, vehicle_pk):
        return get_object_or_404(Vehicle, pk=vehicle_pk, owner=request.user)

    def _get_module(self, module_slug):
        return get_object_or_404(DynamicModule, slug=module_slug, is_enabled=True, garage__isnull=True)

    def _build_form(self, module, data=None, instance_data=None):
        fields_qs = module.fields.order_by("position", "label")
        form = DynamicRecordForm(list(fields_qs), data=data, instance_data=instance_data)
        return form


class DynamicRecordForm(django_forms.Form):
    def __init__(self, module_fields, *args, instance_data=None, **kwargs):
        super().__init__(*args, **kwargs)
        existing = instance_data or {}
        for mf in module_fields:
            self.fields[mf.field_key] = self._make_field(mf)
            if mf.field_key in existing:
                self.initial[mf.field_key] = existing[mf.field_key]

    def _make_field(self, mf):
        base = {"required": mf.is_required, "label": mf.label}
        if mf.field_type == "textarea":
            return django_forms.CharField(
                widget=django_forms.Textarea(attrs={"class": "form-control", "rows": 3}),
                **base,
            )
        if mf.field_type == "number":
            return django_forms.IntegerField(
                widget=django_forms.NumberInput(attrs={"class": "form-control"}), **base
            )
        if mf.field_type == "decimal":
            return django_forms.DecimalField(
                widget=django_forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
                **base,
            )
        if mf.field_type == "date":
            return django_forms.DateField(
                widget=django_forms.DateInput(attrs={"class": "form-control", "type": "date"}),
                **base,
            )
        return django_forms.CharField(
            widget=django_forms.TextInput(attrs={"class": "form-control"}), **base
        )

    def to_storage(self):
        result = {}
        for key, val in self.cleaned_data.items():
            if val is None or val == "":
                result[key] = ""
            elif isinstance(val, datetime.date):
                result[key] = val.isoformat()
            else:
                result[key] = str(val)
        return result


class DynamicRecordListView(LoginRequiredMixin, DynamicModuleMixin, View):
    template_name = "dynamic/record_list.html"

    def get(self, request, vehicle_pk, module_slug):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        raw_records = DynamicRecord.objects.filter(module=module, vehicle=vehicle)
        field_defs = list(module.fields.order_by("position", "label"))
        # Pre-build rows so the template doesn't need dynamic dict lookups
        rows = [
            {
                "pk": r.pk,
                "created_at": r.created_at,
                "values": [r.data.get(fd.field_key, "") for fd in field_defs],
            }
            for r in raw_records
        ]
        return render(
            request,
            self.template_name,
            {
                "vehicle": vehicle,
                "module": module,
                "rows": rows,
                "field_defs": field_defs,
            },
        )


class DynamicRecordCreateView(LoginRequiredMixin, DynamicModuleMixin, View):
    template_name = "dynamic/record_form.html"

    def get(self, request, vehicle_pk, module_slug):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        form = self._build_form(module)
        return render(request, self.template_name, {"vehicle": vehicle, "module": module, "form": form})

    def post(self, request, vehicle_pk, module_slug):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        form = self._build_form(module, data=request.POST)
        if form.is_valid():
            DynamicRecord.objects.create(module=module, vehicle=vehicle, data=form.to_storage())
            messages.success(request, f"{module.name} record added.")
            return redirect("dynamic:list", vehicle_pk=vehicle_pk, module_slug=module_slug)
        return render(request, self.template_name, {"vehicle": vehicle, "module": module, "form": form})


class DynamicRecordUpdateView(LoginRequiredMixin, DynamicModuleMixin, View):
    template_name = "dynamic/record_form.html"

    def _get_record(self, vehicle, module, pk):
        return get_object_or_404(DynamicRecord, pk=pk, vehicle=vehicle, module=module)

    def get(self, request, vehicle_pk, module_slug, pk):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        record = self._get_record(vehicle, module, pk)
        form = self._build_form(module, instance_data=record.data)
        return render(
            request,
            self.template_name,
            {"vehicle": vehicle, "module": module, "form": form, "object": record},
        )

    def post(self, request, vehicle_pk, module_slug, pk):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        record = self._get_record(vehicle, module, pk)
        form = self._build_form(module, data=request.POST, instance_data=record.data)
        if form.is_valid():
            record.data = form.to_storage()
            record.save(update_fields=["data", "updated_at"])
            messages.success(request, f"{module.name} record updated.")
            return redirect("dynamic:list", vehicle_pk=vehicle_pk, module_slug=module_slug)
        return render(
            request,
            self.template_name,
            {"vehicle": vehicle, "module": module, "form": form, "object": record},
        )


class DynamicRecordDeleteView(LoginRequiredMixin, DynamicModuleMixin, View):
    template_name = "dynamic/record_confirm_delete.html"

    def _get_record(self, vehicle, module, pk):
        return get_object_or_404(DynamicRecord, pk=pk, vehicle=vehicle, module=module)

    def get(self, request, vehicle_pk, module_slug, pk):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        record = self._get_record(vehicle, module, pk)
        return render(
            request,
            self.template_name,
            {"vehicle": vehicle, "module": module, "object": record},
        )

    def post(self, request, vehicle_pk, module_slug, pk):
        vehicle = self._get_vehicle(request, vehicle_pk)
        module = self._get_module(module_slug)
        record = self._get_record(vehicle, module, pk)
        record.delete()
        messages.success(request, f"{module.name} record deleted.")
        return redirect("dynamic:list", vehicle_pk=vehicle_pk, module_slug=module_slug)
