import datetime

from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import Vehicle

_CURRENT_YEAR = datetime.date.today().year


class VehicleForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "vehicle"
    year = forms.IntegerField(
        min_value=1886,
        max_value=_CURRENT_YEAR + 1,
        widget=forms.NumberInput(attrs={"placeholder": str(_CURRENT_YEAR)}),
    )

    class Meta:
        model = Vehicle
        fields = (
            "client",
            "make",
            "model",
            "year",
            "license_plate",
            "fuel_type",
            "transmission",
            "color",
            "ccm",
            "hp",
            "engine_code",
            "doors",
            "has_ac",
            "drive_type",
            "vin",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        self._garage = kwargs.pop("garage", None)
        super().__init__(*args, **kwargs)  # ConfigurableFormMixin processes fields here

        labels_hu = {
            "client": "Ügyfél", "make": "Márka", "model": "Modell", "year": "Évjárat",
            "license_plate": "Rendszám", "fuel_type": "Üzemanyag típusa", "transmission": "Váltó",
            "color": "Szín", "ccm": "Motor (ccm)", "hp": "Teljesítmény (LE)",
            "engine_code": "Motorkód", "doors": "Ajtók", "has_ac": "Klíma",
            "drive_type": "Hajtás típusa", "vin": "VIN", "notes": "Megjegyzés"
        }
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        # ── User-filtered Client dropdown ─────────────────────────
        if "client" in self.fields and self._user is not None:
            from apps.clients.models import Client
            self.fields["client"].queryset = Client.objects.filter(user=self._user)
            self.fields["client"].empty_label = "— Nincs ügyfél —"

        # ── Catalog-backed Make dropdown ──────────────────────────
        if "make" in self.fields:
            from apps.catalog.utils import get_active_makes
            make_names = get_active_makes(self._garage)
            current = self.instance.make if (self.instance and self.instance.pk) else ""
            if current and current not in make_names:
                make_names = sorted(set(list(make_names) + [current]))
            make_choices = [("", "— Márka kiválasztása —")] + [(m, m) for m in make_names]
            self.fields["make"].widget = forms.Select(choices=make_choices)

        # ── Catalog-backed Model dropdown (JS narrows to selected make) ──
        if "model" in self.fields:
            from apps.catalog.utils import get_active_models
            make_name = (
                self.data.get("make") or
                (self.instance.make if (self.instance and self.instance.pk) else "")
            )
            model_names = get_active_models(make_name, self._garage) if make_name else []
            # Also load all models so JS can filter client-side
            from apps.catalog.models import CarModel
            from django.db.models import Q
            garage_q = Q(garage__isnull=True)
            if self._garage is not None:
                garage_q |= Q(garage=self._garage)
            all_model_names = list(
                CarModel.objects.filter(garage_q, is_active=True)
                .values_list("name", flat=True)
                .distinct()
            )
            current = self.instance.model if (self.instance and self.instance.pk) else ""
            combined = sorted(set(all_model_names + ([current] if current else [])))
            model_choices = [("", "— Modell kiválasztása —")] + [(m, m) for m in combined]
            self.fields["model"].widget = forms.Select(choices=model_choices)

        # ── Catalog-backed Fuel Type choices ──────────────────────
        if "fuel_type" in self.fields:
            from apps.catalog.utils import get_dropdown_choices
            db = get_dropdown_choices("fuel_type", self._garage)
            if db:
                self.fields["fuel_type"].choices = db

        # ── Catalog-backed Transmission choices ───────────────────
        if "transmission" in self.fields:
            from apps.catalog.utils import get_dropdown_choices
            db = get_dropdown_choices("transmission", self._garage)
            if db:
                self.fields["transmission"].choices = db

        # ── Apply Bootstrap CSS ───────────────────────────────────
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": "form-control", "rows": 3})
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()
