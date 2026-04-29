from django.urls import path

from . import views

app_name = "parts"

urlpatterns = [
    path("", views.PartReplacementListView.as_view(), name="list"),
    path("add/", views.PartReplacementCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PartReplacementDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PartReplacementUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PartReplacementDeleteView.as_view(), name="delete"),
]
