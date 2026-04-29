from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="list"),
    path("upload/", views.DocumentUploadView.as_view(), name="doc-upload"),
    path("<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="doc-delete"),
    path("images/upload/", views.ImageUploadView.as_view(), name="img-upload"),
    path("images/<int:pk>/delete/", views.ImageDeleteView.as_view(), name="img-delete"),
]
