from django import forms
from django.forms import inlineformset_factory

from apps.core.mixins import ConfigurableFormMixin

from .models import Quote, QuoteItem


class QuoteForm(ConfigurableFormMixin, forms.ModelForm):
    form_key = "quote"
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Quote
        fields = ("date", "title", "total_estimate", "notes")

    def __init__(self, *args, **kwargs):
        self._garage = kwargs.pop("garage", None)
        super().__init__(*args, **kwargs)
        labels_hu = {"date": "Dátum", "title": "Cím", "total_estimate": "Becsült végösszeg", "notes": "Megjegyzés"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": "form-control", "rows": 2})
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()


class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = ("service_type", "replacement_part", "part_price", "consumable", "note", "work_hours")

    def __init__(self, *args, **kwargs):
        self._garage = kwargs.pop("garage", None)
        super().__init__(*args, **kwargs)

        from apps.catalog.utils import get_dropdown_choices
        from apps.services.models import ServiceRecord

        service_choices = get_dropdown_choices("service_type", self._garage) or list(ServiceRecord.SERVICE_CHOICES)
        consumable_choices = get_dropdown_choices("consumables", self._garage)

        current_service = self.instance.service_type if (self.instance and self.instance.pk) else ""
        current_consumable = self.instance.consumable if (self.instance and self.instance.pk) else ""
        service_values = {value for value, _label in service_choices}
        consumable_values = {value for value, _label in consumable_choices}
        if current_service and current_service not in service_values:
            service_choices = list(service_choices) + [(current_service, current_service)]
        if current_consumable and current_consumable not in consumable_values:
            consumable_choices = list(consumable_choices) + [(current_consumable, current_consumable)]

        labels_hu = {"service_type": "Szerviztípus", "replacement_part": "Cserélt alkatrész", "part_price": "Alkatrész ára", "consumable": "Fogyóanyag", "note": "Megjegyzés", "work_hours": "Munkaóra"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label

        self.fields["service_type"].choices = [("", "— Szerviztípus kiválasztása —")] + list(service_choices)
        self.fields["consumable"].widget = forms.Select(
            choices=[("", "— Fogyóanyag kiválasztása —")] + list(consumable_choices)
        )

        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({"class": "form-control", "rows": 1})
            else:
                widget.attrs["class"] = "form-control"
            if field_name in {"part_price", "work_hours"}:
                widget.attrs.setdefault("step", "0.01")


class BaseQuoteItemFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.garage = kwargs.pop("garage", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["garage"] = self.garage
        return kwargs

    def clean(self):
        super().clean()
        non_deleted = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if not non_deleted:
            raise forms.ValidationError("Legalább egy árajánlat sort adjon meg.")


QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    formset=BaseQuoteItemFormSet,
    extra=1,
    can_delete=True,
)
