from .models import Garage, GarageMembership


def get_user_garages(user):
    """Return all Garage instances the user belongs to (any role)."""
    return Garage.objects.filter(memberships__user=user).distinct()


def is_garage_member(user, garage):
    """Return True if the user has any membership in the given garage."""
    return GarageMembership.objects.filter(user=user, garage=garage).exists()


def get_active_garage(request):
    """Return the active Garage for the current request, or None.

    Priority: session-stored ID → first active membership.
    """
    if not request.user.is_authenticated:
        return None
    garage_id = request.session.get("active_garage_id")
    if garage_id:
        try:
            return Garage.objects.get(pk=garage_id, memberships__user=request.user, is_active=True)
        except Garage.DoesNotExist:
            pass
    return Garage.objects.filter(memberships__user=request.user, is_active=True).first()
