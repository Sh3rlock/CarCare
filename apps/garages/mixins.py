from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Garage
from . import permissions as garage_perms


class GarageResolveMixin:
    """
    Resolves the Garage from the 'garage_slug' URL kwarg and verifies
    the request user is a member. Raises Http404 for both missing garages
    and non-members — same pattern as VehicleOwnerMixin, so existence is
    never leaked to outsiders.

    Always combine with LoginRequiredMixin on the view class.
    Result is cached on the instance (one DB hit per request).
    """

    garage_url_kwarg = "garage_slug"

    def get_garage(self):
        if not hasattr(self, "_garage"):
            garage = get_object_or_404(Garage, slug=self.kwargs[self.garage_url_kwarg])
            if not garage_perms.can_read(self.request.user, garage):
                raise Http404
            self._garage = garage
        return self._garage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["garage"] = self.get_garage()
        return context


class GarageWriteMixin(GarageResolveMixin):
    """Mechanic role or above: may create and edit records."""

    def dispatch(self, request, *args, **kwargs):
        if not garage_perms.can_write_records(request.user, self.get_garage()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GarageDeleteMixin(GarageResolveMixin):
    """Admin role or above: may delete records."""

    def dispatch(self, request, *args, **kwargs):
        if not garage_perms.can_delete_records(request.user, self.get_garage()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GarageAdminMixin(GarageResolveMixin):
    """Admin role or above: may manage garage membership."""

    def dispatch(self, request, *args, **kwargs):
        if not garage_perms.can_manage_members(request.user, self.get_garage()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GarageOwnerMixin(GarageResolveMixin):
    """Owner role only: may rename, delete, or transfer the garage."""

    def dispatch(self, request, *args, **kwargs):
        if not garage_perms.can_manage_garage(request.user, self.get_garage()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
