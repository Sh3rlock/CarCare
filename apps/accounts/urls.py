from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import path

from . import views
from .forms import StyledAuthenticationForm, StyledPasswordChangeForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
            authentication_form=StyledAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile-edit"),
    path(
        "password/change/",
        PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            form_class=StyledPasswordChangeForm,
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
]
