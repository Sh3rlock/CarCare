from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # API
    path("api/models/", views.models_for_make_api, name="api_models"),
    path("api/makes/quick-add/", views.make_quick_add_api, name="api_make_quick_add"),
    path("api/models/quick-add/", views.model_quick_add_api, name="api_model_quick_add"),
    path(
        "api/dropdowns/<str:list_key>/quick-add/",
        views.dropdown_choice_quick_add_api,
        name="api_dropdown_choice_quick_add",
    ),

    # Makes
    path("makes/", views.CarMakeListView.as_view(), name="make_list"),
    path("makes/add/", views.CarMakeCreateView.as_view(), name="make_add"),
    path("makes/<int:pk>/edit/", views.CarMakeUpdateView.as_view(), name="make_edit"),
    path("makes/<int:pk>/delete/", views.CarMakeDeleteView.as_view(), name="make_delete"),

    # Models (nested under make)
    path("makes/<int:make_pk>/models/", views.CarModelListView.as_view(), name="model_list"),
    path("makes/<int:make_pk>/models/add/", views.CarModelCreateView.as_view(), name="model_add"),
    path("makes/<int:make_pk>/models/<int:pk>/edit/", views.CarModelUpdateView.as_view(), name="model_edit"),
    path("makes/<int:make_pk>/models/<int:pk>/delete/", views.CarModelDeleteView.as_view(), name="model_delete"),

    # Dropdown choices
    path("dropdowns/", views.DropdownListView.as_view(), name="dropdown_list"),
    path("service-types/", views.ServiceTypesListView.as_view(), name="service_types_list"),
    path("consumables/", views.ConsumablesListView.as_view(), name="consumables_list"),
    path("dropdowns/<str:list_key>/add/", views.DropdownChoiceCreateView.as_view(), name="dropdown_choice_add"),
    path("dropdowns/<str:list_key>/<int:pk>/edit/", views.DropdownChoiceUpdateView.as_view(), name="dropdown_choice_edit"),
    path("dropdowns/<str:list_key>/<int:pk>/delete/", views.DropdownChoiceDeleteView.as_view(), name="dropdown_choice_delete"),
]
