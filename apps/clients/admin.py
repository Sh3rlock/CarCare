from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("__str__", "email", "phone", "user")
    search_fields = ("first_name", "last_name", "company", "email")
    list_filter = ("user",)
