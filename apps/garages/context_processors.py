from apps.formconfig.utils import get_enabled_modules

from .models import GarageMembership
from .utils import get_active_garage


def garage_context(request):
    if not request.user.is_authenticated:
        return {"enabled_modules": set()}
    garage = get_active_garage(request)
    is_owner = (
        garage is not None and
        GarageMembership.objects.filter(
            user=request.user, garage=garage, role=GarageMembership.Role.OWNER
        ).exists()
    )
    return {
        "active_garage": garage,
        "is_garage_owner": is_owner,
        "enabled_modules": get_enabled_modules(garage),
    }
