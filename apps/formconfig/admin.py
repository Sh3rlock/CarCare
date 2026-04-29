from django.contrib import admin

from .models import BuiltinFieldConfig, CustomField

admin.site.register(BuiltinFieldConfig)
admin.site.register(CustomField)
