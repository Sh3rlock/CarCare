from .models import GarageMembership
from .utils import get_active_garage


def garage_context(request):
    if not request.user.is_authenticated:
        return {}
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
    }
