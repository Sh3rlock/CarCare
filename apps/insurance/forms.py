from django import forms

from apps.core.mixins import ConfigurableFormMixin

from .models import InsurancePolicy


class InsurancePolicyForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "insurance"
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = InsurancePolicy
        fields = (
            "provider",
            "policy_number",
            "coverage_type",
            "start_date",
            "end_date",
            "premium",
            "premium_period",
            "agent_name",
            "agent_phone",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {
            "provider": "Szolgáltató", "policy_number": "Kötvényszám", "coverage_type": "Fedezet típusa",
            "start_date": "Kezdő dátum", "end_date": "Záró dátum", "premium": "Díj",
            "premium_period": "Díjfizetés gyakorisága", "agent_name": "Ügyintéző neve",
            "agent_phone": "Ügyintéző telefonszáma", "notes": "Megjegyzés"
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

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end <= start:
            self.add_error("end_date", "A záró dátumnak a kezdő dátum után kell lennie.")
        return cleaned_data
