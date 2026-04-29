from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.ServiceRecordListView.as_view(), name="list"),
    path("add/", views.ServiceRecordCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ServiceRecordDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", views.ServiceRecordPDFView.as_view(), name="pdf"),
    path("<int:pk>/edit/", views.ServiceRecordUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ServiceRecordDeleteView.as_view(), name="delete"),
]
