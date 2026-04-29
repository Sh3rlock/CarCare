from django.urls import path

from . import views

app_name = "formconfig"

urlpatterns = [
    # Form Builder home
    path("", views.FormAdminListView.as_view(), name="form_list"),

    # Built-in module toggle
    path("modules/<str:module_key>/toggle/", views.ToggleModuleView.as_view(), name="toggle_module"),

    # Dynamic module CRUD
    path("dynamic/add/", views.DynamicModuleCreateView.as_view(), name="dynamic_module_add"),
    path("dynamic/<int:pk>/edit/", views.DynamicModuleUpdateView.as_view(), name="dynamic_module_edit"),
    path("dynamic/<int:pk>/delete/", views.DynamicModuleDeleteView.as_view(), name="dynamic_module_delete"),
    path("dynamic/<int:pk>/toggle/", views.ToggleDynamicModuleView.as_view(), name="dynamic_module_toggle"),

    # Dynamic module field management
    path("dynamic/<int:pk>/fields/", views.DynamicModuleFieldsView.as_view(), name="dynamic_module_fields"),
    path("dynamic/<int:pk>/fields/add/", views.DynamicModuleFieldCreateView.as_view(), name="dynamic_field_add"),
    path("dynamic/<int:pk>/fields/<int:field_pk>/edit/", views.DynamicModuleFieldUpdateView.as_view(), name="dynamic_field_edit"),
    path("dynamic/<int:pk>/fields/<int:field_pk>/delete/", views.DynamicModuleFieldDeleteView.as_view(), name="dynamic_field_delete"),

    # Built-in form field configuration
    path("<str:form_key>/", views.ManageFormFieldsView.as_view(), name="form_fields"),
    path("<str:form_key>/fields/<str:field_name>/toggle/", views.ToggleFieldVisibilityView.as_view(), name="toggle_field"),
    path("<str:form_key>/custom/add/", views.CustomFieldCreateView.as_view(), name="custom_field_add"),
    path("<str:form_key>/custom/<int:pk>/edit/", views.CustomFieldUpdateView.as_view(), name="custom_field_edit"),
    path("<str:form_key>/custom/<int:pk>/delete/", views.CustomFieldDeleteView.as_view(), name="custom_field_delete"),
]
