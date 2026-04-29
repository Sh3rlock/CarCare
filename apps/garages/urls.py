from django.urls import path

from . import views

app_name = "garages"

urlpatterns = [
    # ── Garage list & create ──────────────────────────────────
    path("", views.GarageListView.as_view(), name="list"),
    path("new/", views.GarageCreateView.as_view(), name="create"),

    # ── Garage detail / edit / delete ─────────────────────────
    path("<slug:garage_slug>/", views.GarageDashboardView.as_view(), name="dashboard"),
    path("<slug:garage_slug>/edit/", views.GarageUpdateView.as_view(), name="update"),
    path("<slug:garage_slug>/delete/", views.GarageDeleteView.as_view(), name="delete"),

    # ── Vehicles ──────────────────────────────────────────────
    path("<slug:garage_slug>/vehicles/", views.GarageVehicleListView.as_view(), name="vehicles"),

    # ── Members ───────────────────────────────────────────────
    path("<slug:garage_slug>/members/", views.GarageMemberListView.as_view(), name="members"),
    path("<slug:garage_slug>/members/<int:pk>/role/", views.GarageChangeMemberRoleView.as_view(), name="member_role"),
    path("<slug:garage_slug>/members/<int:pk>/remove/", views.GarageRemoveMemberView.as_view(), name="member_remove"),

    # ── Settings overview ─────────────────────────────────────
    path("<slug:garage_slug>/settings/", views.GarageSettingsView.as_view(), name="settings"),
    path("<slug:garage_slug>/settings/modules/<str:module_key>/toggle/", views.GarageToggleModuleView.as_view(), name="toggle_module"),

    # ── Per-garage form field config ──────────────────────────
    path("<slug:garage_slug>/settings/forms/<str:form_key>/", views.GarageFormFieldsView.as_view(), name="form_fields"),
    path("<slug:garage_slug>/settings/forms/<str:form_key>/fields/<str:field_name>/toggle/", views.GarageToggleFieldView.as_view(), name="toggle_field"),
    path("<slug:garage_slug>/settings/forms/<str:form_key>/custom/add/", views.GarageCustomFieldCreateView.as_view(), name="custom_field_create"),
    path("<slug:garage_slug>/settings/forms/<str:form_key>/custom/<int:pk>/edit/", views.GarageCustomFieldUpdateView.as_view(), name="custom_field_update"),
    path("<slug:garage_slug>/settings/forms/<str:form_key>/custom/<int:pk>/delete/", views.GarageCustomFieldDeleteView.as_view(), name="custom_field_delete"),

    # ── Per-garage dynamic modules ────────────────────────────
    path("<slug:garage_slug>/settings/dynamic/add/", views.GarageDynamicModuleCreateView.as_view(), name="dynamic_module_create"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/edit/", views.GarageDynamicModuleUpdateView.as_view(), name="dynamic_module_update"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/delete/", views.GarageDynamicModuleDeleteView.as_view(), name="dynamic_module_delete"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/toggle/", views.GarageToggleDynamicModuleView.as_view(), name="toggle_dynamic_module"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/fields/", views.GarageDynamicModuleFieldsView.as_view(), name="dynamic_module_fields"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/fields/add/", views.GarageDynamicFieldCreateView.as_view(), name="dynamic_field_create"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/fields/<int:field_pk>/edit/", views.GarageDynamicFieldUpdateView.as_view(), name="dynamic_field_update"),
    path("<slug:garage_slug>/settings/dynamic/<int:pk>/fields/<int:field_pk>/delete/", views.GarageDynamicFieldDeleteView.as_view(), name="dynamic_field_delete"),
]
