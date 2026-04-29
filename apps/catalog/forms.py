from django import forms
from django.utils.text import slugify

from .models import CarMake, CarModel, DropdownChoice


class CarMakeForm(forms.ModelForm):
    class Meta:
        model = CarMake
        fields = ("name", "is_active", "position")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.NumberInput(attrs={"class": "form-control"}),
        }


class CarModelForm(forms.ModelForm):
    class Meta:
        model = CarModel
        fields = ("name", "is_active", "position")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.NumberInput(attrs={"class": "form-control"}),
        }


class DropdownChoiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.list_key = kwargs.pop("list_key", None)
        super().__init__(*args, **kwargs)
        if self.list_key == "consumables":
            self.fields.pop("value", None)

    def _build_value(self):
        label = (self.cleaned_data.get("label") or "").strip()
        return slugify(label).replace("-", "_")[:50]

    def clean(self):
        cleaned_data = super().clean()
        if self.list_key == "consumables":
            value = self._build_value()
            if not value:
                self.add_error("label", "A fogyóanyag neve kötelező.")
            else:
                self.instance.value = value
        return cleaned_data

    class Meta:
        model = DropdownChoice
        fields = ("value", "label", "is_active", "position")
        widgets = {
            "value": forms.TextInput(attrs={"class": "form-control"}),
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.NumberInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "value": "Rövid belső kulcs az adatbázisban (pl. benzin, elektromos). Max. 50 karakter.",
        }
