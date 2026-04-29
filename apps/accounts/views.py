from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from apps.garages.models import Garage, GarageMembership

from .forms import ProfileForm, RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            garage = Garage.objects.create(
                name=form.cleaned_data["garage_name"],
                owner=user,
            )
            GarageMembership.objects.create(
                user=user,
                garage=garage,
                role=GarageMembership.Role.OWNER,
            )
        login(request, user)
        messages.success(request, f'Welcome to CarCare! Your garage "{garage.name}" is ready.')
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    user_profile = request.user.profile
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=user_profile,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile_edit.html", {"form": form})
