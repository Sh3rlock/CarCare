from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

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

# User uploads: served here in development (DEBUG) or when SERVE_MEDIA is True.
# In production, prefer nginx (or similar) to alias /media/ to MEDIA_ROOT; set SERVE_MEDIA=0 then.
if settings.DEBUG or getattr(settings, "SERVE_MEDIA", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
