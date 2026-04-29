from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import User, UserProfile


def _bootstrap(form):
    """Add form-control class to every widget — avoids widget_tweaks dependency."""
    for field in form.fields.values():
        widget = field.widget
        css = widget.attrs.get("class", "")
        widget.attrs["class"] = (css + " form-control").strip()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    garage_name = forms.CharField(
        max_length=200,
        label="Garázs / szerviz neve",
        widget=forms.TextInput(attrs={"placeholder": "pl. Minta Autószerviz"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "garage_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hints hidden until validation fails (errors render in red on the field)
        self.fields["username"].help_text = ""
        self.fields["username"].label = "Felhasználónév"
        self.fields["email"].label = "Email cím"
        self.fields["password1"].label = "Jelszó"
        self.fields["password2"].label = "Jelszó megerősítése"
        self.fields["garage_name"].label = "Garázs / szerviz neve"
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
        _bootstrap(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ("phone", "avatar")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["first_name"].label = "Keresztnév"
        self.fields["last_name"].label = "Vezetéknév"
        self.fields["email"].label = "Email cím"
        self.fields["phone"].label = "Telefonszám"
        self.fields["avatar"].label = "Profilkép"
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
        _bootstrap(self)
        # Avatar uses file input — override the class so it renders correctly
        self.fields["avatar"].widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Jelenlegi jelszó"
        self.fields["new_password1"].label = "Új jelszó"
        self.fields["new_password2"].label = "Új jelszó megerősítése"
        _bootstrap(self)


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Felhasználónév"
        self.fields["password"].label = "Jelszó"
        _bootstrap(self)
