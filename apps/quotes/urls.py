from django.urls import path

from . import views

app_name = "quotes"

urlpatterns = [
    path("", views.QuoteListView.as_view(), name="list"),
    path("add/", views.QuoteCreateView.as_view(), name="create"),
    path("<int:pk>/", views.QuoteDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", views.QuotePDFView.as_view(), name="pdf"),
    path("<int:pk>/convert-to-service/", views.QuoteConvertToServiceView.as_view(), name="convert_to_service"),
    path("<int:pk>/edit/", views.QuoteUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.QuoteDeleteView.as_view(), name="delete"),
]
