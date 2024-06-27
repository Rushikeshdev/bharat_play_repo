from django.contrib import admin

# Register your models here.

from .models import *
from django.apps import apps


app = apps.get_app_config('bank_account_pe')
for model_name, model in app.models.items():
   
    if model_name == 'accountstatement':
           
            admin_class = type('AccountStatementAdmin', (admin.ModelAdmin,), {
                'list_display': ('account', 'trn_date', 'deposit', 'withdraw', 'updated_at'),
                'list_filter': ('account', 'trn_date', 'updated_at'),
                'search_fields': ('account__ammount',),  # Adjust with actual field used for search
            })
            admin.site.register(model, admin_class)
    else:
            admin.site.register(model)



