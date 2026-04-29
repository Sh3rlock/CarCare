import os

from django import forms

from .models import VehicleDocument, VehicleImage

_10MB = 10 * 1024 * 1024
_5MB = 5 * 1024 * 1024

_ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv"}
_ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _bootstrap(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.Select):
            widget.attrs["class"] = "form-select"
        elif isinstance(widget, forms.Textarea):
            widget.attrs.update({"class": "form-control", "rows": 3})
        else:
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = (existing + " form-control").strip()


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = VehicleDocument
        fields = ("title", "doc_type", "file", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {"title": "Cím", "doc_type": "Dokumentum típusa", "file": "Fájl", "notes": "Megjegyzés"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label
        _bootstrap(self)

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            if hasattr(f, "size") and f.size > _10MB:
                raise forms.ValidationError("A fájl túl nagy. A maximális méret 10 MB.")
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in _ALLOWED_DOC_EXTENSIONS:
                allowed = ", ".join(sorted(_ALLOWED_DOC_EXTENSIONS))
                raise forms.ValidationError(f"Nem támogatott fájltípus. Engedélyezett: {allowed}")
        return f


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = VehicleImage
        fields = ("title", "image")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels_hu = {"title": "Felirat", "image": "Fénykép"}
        for key, label in labels_hu.items():
            if key in self.fields:
                self.fields[key].label = label
        _bootstrap(self)

    def clean_image(self):
        img = self.cleaned_data.get("image")
        if img:
            if hasattr(img, "size") and img.size > _5MB:
                raise forms.ValidationError("A kép túl nagy. A maximális méret 5 MB.")
            ext = os.path.splitext(img.name)[1].lower()
            if ext not in _ALLOWED_IMAGE_EXTENSIONS:
                allowed = ", ".join(sorted(_ALLOWED_IMAGE_EXTENSIONS))
                raise forms.ValidationError(f"Nem támogatott fájltípus. Engedélyezett: {allowed}")
        return img
