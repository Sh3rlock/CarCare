from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import PartReplacement


class PartReplacementForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "part"
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    next_replacement_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = PartReplacement
        fields = (
            "part_type",
            "part_name",
            "part_number",
            "brand",
            "date",
            "mileage_at_replacement",
            "next_replacement_mileage",
            "next_replacement_date",
            "cost",
            "workshop",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {
            "part_type": "Alkatrész típusa", "part_name": "Alkatrész neve", "part_number": "Cikkszám",
            "brand": "Márka", "date": "Csere dátuma", "mileage_at_replacement": "Km állás cserekor",
            "next_replacement_mileage": "Következő csere km állása", "next_replacement_date": "Következő csere dátuma",
            "cost": "Költség", "workshop": "Szerviz", "notes": "Megjegyzés"
        }
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": "form-control", "rows": 3})
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()
