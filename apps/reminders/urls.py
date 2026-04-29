from django.urls import path

from . import views

app_name = "reminders"

urlpatterns = [
    path("", views.ReminderListView.as_view(), name="list"),
    path("add/", views.ReminderCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.ReminderUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ReminderDeleteView.as_view(), name="delete"),
    path("<int:pk>/toggle/", views.ReminderToggleView.as_view(), name="toggle"),
]
