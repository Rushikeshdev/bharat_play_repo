from django.contrib import admin

# Register your models here.

from .models import *
from django.apps import apps


app = apps.get_app_config('bank_account_pe')
for model_name, model in app.models.items():
    admin.site.register(model)
