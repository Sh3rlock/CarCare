from django.urls import path

from . import views

app_name = "mileage"

urlpatterns = [
    path("", views.MileageLogListView.as_view(), name="list"),
    path("add/", views.MileageLogCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.MileageLogUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.MileageLogDeleteView.as_view(), name="delete"),
]
