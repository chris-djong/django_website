from django.db import models
from django.contrib.auth.models import User
import datetime

# Simple model to store the API key
class Stockkey(models.Model):
    key = models.CharField(max_length=50)

class CurrencyTicker(models.Model):
    name = models.CharField(max_length=50, unique=True)
    ticker = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

# Historical currency values
class CurrencyHistory(models.Model):
    currency = models.ForeignKey(CurrencyTicker, on_delete=models.CASCADE)
    date = models.DateField()
    to_eur = models.FloatField()

    def __str__(self):
        return "%s - %s" % (self.currency, self.date)

# Stock Model
class Stock(models.Model):
    ticker = models.CharField(max_length=50, unique=True)
    article_ticker = models.CharField(max_length=50, null=True, blank=True)
    plot_ticker = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    currency = models.ForeignKey(CurrencyTicker, on_delete=models.CASCADE)

    n_articles_avg = models.IntegerField(default=0)

    def __str__(self):
        if self.name is None:
            return "%s" % (self.ticker)
        else:
            return "%s" % (self.name)

    class Meta:
        ordering = ["name"]

# Model keeping track of the user portfolio history
# Price keeps track of the total (all your stocks time their price)
# Profit keeps track of the current profit (whatever you win, so net-invested)
# Invested is the amount that has been invested (thus stocks + price_bought + price_sold)
# Net the the price minus the sell fees (so what we have actually have on our account)
# Cash keeps track of the past profit. So whenver a stock is sold its profit or loss is added to the cash
class UserPortfolioHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    price = models.FloatField()
    profit = models.FloatField()
    invested = models.FloatField()
    net = models.FloatField()
    cash = models.FloatField()

    def __str__(self):
        name = str(self.user) +" - " + str(self.date)
        return name


# Model for the price history och each stock
class StockPriceHistory(models.Model):
    ticker = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()

    # Open Low High Close Storage
    o = models.FloatField(null=True)
    l = models.FloatField(null=True)
    h = models.FloatField(null=True)
    c = models.FloatField(null=True)
    v = models.FloatField(null=True)

    def __str__(self):
        name = str(self.ticker) +" - " + str(self.date)
        return name

# Create your models here.
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    portfolio = models.CharField(max_length=100, default="Portfolio")
    amount = models.FloatField()
    label = models.CharField(max_length=1000, null=True, blank=True)
    # This boolean is only used to check whether the transaction is a merged transaction in the overview. This makes it possible to handle the settings and plots for example 
    combined = models.BooleanField(default=False)
    # In case we have a split totals are calculated differently
    is_split = models.BooleanField(default=False)
    date_bought = models.DateField()
    price_bought = models.FloatField(null=True, blank=True)
    date_sold = models.DateField(null=True, blank=True)
    price_sold = models.FloatField(null=True, blank=True)

    buy_fees = models.FloatField(blank=True)
    buy_fees_constant = models.FloatField(default=0, blank=True)
    buy_fees_linear = models.FloatField(default=0, blank=True)
    sell_fees = models.FloatField(blank=True)
    sell_fees_constant = models.FloatField(default=0, blank=True)
    sell_fees_linear = models.FloatField(default=0, blank=True)

    lower_alert = models.FloatField(null=True, blank=True)
    upper_alert = models.FloatField(null=True, blank=True)

    def __str__(self):
      return "%s - %s" % (self.stock, self.user)

