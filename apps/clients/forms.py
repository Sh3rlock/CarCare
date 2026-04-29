from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import Client


class ClientForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "client"

    class Meta:
        model = Client
        fields = ("first_name", "last_name", "company", "email", "phone", "address", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {"first_name": "Keresztnév", "last_name": "Vezetéknév", "company": "Cég", "email": "Email cím", "phone": "Telefonszám", "address": "Cím", "notes": "Megjegyzés"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": "form-control", "rows": 3})
            else:
                widget.attrs["class"] = "form-control"
