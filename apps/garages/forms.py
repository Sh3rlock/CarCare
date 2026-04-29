from django import forms

from apps.formconfig.models import CustomField, DynamicModule, DynamicModuleField

from .models import Garage, GarageMembership


class GarageForm(forms.ModelForm):
    class Meta:
        model = Garage
        fields = ("name", "slug")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["name"].label = "Garázs neve"
        self.fields["slug"].label = "Slug"
        self.fields["slug"].help_text = "URL-barát azonosító (automatikusan kitöltve). Módosítása megszakíthatja a meglévő linkeket."


class GarageInviteForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=254,
        label="Felhasználónév vagy email",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "felhasznalonev vagy email@pelda.hu"}),
    )
    role = forms.ChoiceField(
        choices=GarageMembership.Role.choices,
        initial=GarageMembership.Role.STAFF,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class GarageCreateMemberForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Felhasználónév",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "uj.felhasznalonev"}),
    )
    email = forms.EmailField(
        required=False,
        label="Email cím",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "felhasznalo@pelda.hu"}),
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Keresztnév",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Vezetéknév",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Ideiglenes jelszó",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Kezdeti jelszó megadása"}),
        help_text="A tag első bejelentkezés után változtassa meg ezt a jelszót.",
    )
    role = forms.ChoiceField(
        choices=GarageMembership.Role.choices,
        initial=GarageMembership.Role.STAFF,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class GarageCustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ("label", "field_type", "is_required", "is_visible", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


class GarageDynamicModuleForm(forms.ModelForm):
    class Meta:
        model = DynamicModule
        fields = ("name", "slug", "description", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "A név alapján automatikusan kitöltve."


class GarageDynamicModuleFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicModuleField
        fields = ("label", "field_type", "is_required", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )
