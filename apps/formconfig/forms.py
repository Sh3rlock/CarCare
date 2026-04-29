from django import forms

from .models import CustomField, DynamicModule, DynamicModuleField


def _bootstrap(form):
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.Select):
            widget.attrs["class"] = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "form-check-input"
        else:
            widget.attrs["class"] = "form-control"


class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ("label", "field_type", "is_required", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self)


class DynamicModuleForm(forms.ModelForm):
    class Meta:
        model = DynamicModule
        fields = ("name", "description", "is_enabled", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self)


class DynamicModuleFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicModuleField
        fields = ("label", "field_type", "is_required", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap(self)
