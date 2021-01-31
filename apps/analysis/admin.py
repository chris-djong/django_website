from django.contrib import admin
from .models import IexApiKey, KeyStats, BalanceSheet, CashFlow, IncomeStatement


# Register your models here.
admin.site.register(IexApiKey)
admin.site.register(KeyStats)
admin.site.register(BalanceSheet)
admin.site.register(IncomeStatement)
admin.site.register(CashFlow)
