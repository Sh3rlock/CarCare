from django.urls import path

from . import views

app_name = "insurance"

urlpatterns = [
    path("", views.InsurancePolicyListView.as_view(), name="list"),
    path("add/", views.InsurancePolicyCreateView.as_view(), name="create"),
    path("<int:pk>/", views.InsurancePolicyDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.InsurancePolicyUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.InsurancePolicyDeleteView.as_view(), name="delete"),
]
