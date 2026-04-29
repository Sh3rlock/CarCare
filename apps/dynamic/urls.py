from django.urls import path

from . import views

app_name = "dynamic"

urlpatterns = [
    path("<slug:module_slug>/", views.DynamicRecordListView.as_view(), name="list"),
    path("<slug:module_slug>/add/", views.DynamicRecordCreateView.as_view(), name="create"),
    path("<slug:module_slug>/<int:pk>/edit/", views.DynamicRecordUpdateView.as_view(), name="update"),
    path("<slug:module_slug>/<int:pk>/delete/", views.DynamicRecordDeleteView.as_view(), name="delete"),
]
