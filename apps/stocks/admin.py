from django.contrib import admin
from .models import Transaction, Stock, CurrencyTicker, CurrencyHistory, StockPriceHistory, Stockkey, UserPortfolioHistory

# Register your models here.
admin.site.register(Transaction)
admin.site.register(Stock)
admin.site.register(StockPriceHistory)
admin.site.register(Stockkey)
admin.site.register(UserPortfolioHistory)
admin.site.register(CurrencyHistory)
admin.site.register(CurrencyTicker)
