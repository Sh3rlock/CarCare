from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import MileageLog


class MileageLogForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "mileage"
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = MileageLog
        fields = ("date", "odometer", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {"date": "Dátum", "odometer": "Kilométeróra állás", "notes": "Megjegyzés"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()
