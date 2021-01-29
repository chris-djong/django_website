from django.contrib import admin
from .models import IexApiKey, BalanceSheet


# Register your models here.
admin.site.register(IexApiKey)
admin.site.register(BalanceSheet)
