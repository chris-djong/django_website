from django.contrib import admin
from .models import IexApiKey, KeyStats, BalanceSheet


# Register your models here.
admin.site.register(IexApiKey)
admin.site.register(KeyStats)
admin.site.register(BalanceSheet)
