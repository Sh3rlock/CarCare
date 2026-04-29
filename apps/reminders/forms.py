from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import Reminder


class ReminderForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "reminder"
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Reminder
        fields = ("title", "due_date", "due_mileage", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {"title": "Cím", "due_date": "Esedékesség dátuma", "due_mileage": "Esedékes km állás", "notes": "Megjegyzés"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()
