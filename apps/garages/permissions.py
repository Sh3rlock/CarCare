from .models import GarageMembership

# Role matrix:
# action              | owner | admin | mechanic | staff
# --------------------|-------|-------|----------|------
# read data           |   ✓   |   ✓   |    ✓     |   ✓
# create / edit       |   ✓   |   ✓   |    ✓     |   ✗
# delete records      |   ✓   |   ✓   |    ✗     |   ✗
# manage members      |   ✓   |   ✓   |    ✗     |   ✗
# manage garage       |   ✓   |   ✗   |    ✗     |   ✗

_WRITE_ROLES = frozenset({
    GarageMembership.Role.OWNER,
    GarageMembership.Role.ADMIN,
    GarageMembership.Role.MECHANIC,
})
_ADMIN_ROLES = frozenset({
    GarageMembership.Role.OWNER,
    GarageMembership.Role.ADMIN,
})
_OWNER_ROLES = frozenset({GarageMembership.Role.OWNER})


def get_role(user, garage):
    """Return the user's role string for this garage, or None if not a member."""
    try:
        return GarageMembership.objects.values_list("role", flat=True).get(
            user=user, garage=garage
        )
    except GarageMembership.DoesNotExist:
        return None


def can_read(user, garage):
    """Any garage member may read data."""
    return GarageMembership.objects.filter(user=user, garage=garage).exists()


def can_write_records(user, garage):
    """Mechanic role or above may create and edit records."""
    return get_role(user, garage) in _WRITE_ROLES


def can_delete_records(user, garage):
    """Admin role or above may delete records."""
    return get_role(user, garage) in _ADMIN_ROLES


def can_manage_members(user, garage):
    """Admin role or above may invite/remove/change member roles."""
    return get_role(user, garage) in _ADMIN_ROLES


def can_manage_garage(user, garage):
    """Only the garage owner may rename, delete, or transfer the garage."""
    return get_role(user, garage) in _OWNER_ROLES
