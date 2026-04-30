import re
from urllib.parse import urlparse

from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.urls import path, include, re_path
from django.views.static import serve

from apps.dashboard.views import DashboardView, GlobalSearchView, HelpView
from apps.accounts.forms import StyledAuthenticationForm
from apps.services.views import GlobalServiceHistoryView
from apps.quotes.views import GlobalQuoteHistoryView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
            authentication_form=StyledAuthenticationForm,
        ),
        name="landing",
    ),
    path("accounts/", include("apps.accounts.urls")),
    path("segitseg/", HelpView.as_view(), name="help"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("search/", GlobalSearchView.as_view(), name="global_search"),
    path("services/", GlobalServiceHistoryView.as_view(), name="services_history"),
    path("quotes/", GlobalQuoteHistoryView.as_view(), name="quotes_history"),
    path("vehicles/", include("apps.vehicles.urls")),
    path("vehicles/<int:vehicle_pk>/services/", include("apps.services.urls")),
    path("vehicles/<int:vehicle_pk>/quotes/", include("apps.quotes.urls")),
    path("vehicles/<int:vehicle_pk>/parts/", include("apps.parts.urls")),
    path("vehicles/<int:vehicle_pk>/mileage/", include("apps.mileage.urls")),
    path("vehicles/<int:vehicle_pk>/insurance/", include("apps.insurance.urls")),
    path("vehicles/<int:vehicle_pk>/documents/", include("apps.documents.urls")),
    path("vehicles/<int:vehicle_pk>/reminders/", include("apps.reminders.urls")),
    path("vehicles/<int:vehicle_pk>/dynamic/", include("apps.dynamic.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("form-admin/", include("apps.formconfig.urls")),
    path("clients/", include("apps.clients.urls")),
    path("garages/", include("apps.garages.urls")),
]

# User uploads. ``django.conf.urls.static.static()`` intentionally returns NO patterns when
# DEBUG is False (see Django docs), so ``static(MEDIA_URL, …)`` never mounted /media/ in
# production. Use an explicit ``serve`` route when serving files from Django.
_serve_media = settings.DEBUG or getattr(settings, "SERVE_MEDIA", True)
_media_url = settings.MEDIA_URL or ""
_parsed_media = urlparse(_media_url)
# Skip local mount when MEDIA_URL is absolute (S3, CDN, or //host/…).
if _serve_media and _media_url and not (
    _parsed_media.scheme in ("http", "https") or _parsed_media.netloc
):
    prefix = _media_url.lstrip("/")
    if prefix:
        urlpatterns += [
            re_path(
                r"^%s(?P<path>.*)$" % re.escape(prefix),
                serve,
                {"document_root": str(settings.MEDIA_ROOT)},
            ),
        ]
