from django.db import models
from ..stocks.models import Stock

# Model for the price history och each stock
class IndicatorHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()

    acc_dist = models.FloatField()  # accumulation distribution indicator
    bollinger_upper = models.FloatField()  # upper bollinger band
    bollinger_middle = models.FloatField()  # middle bollinger band
    bollinger_lower = models.FloatField()  # lower bollinger band
    macd = models.FloatField()  # moving average convergence divergence
    macd_signal = models.FloatField()  # a nine day ema of macd
    stochastic = models.FloatField()  # stochastic oscillator
    rsi = models.FloatField()  # relative strength index
    aroon_down = models.FloatField() # upper aroon indicator
    aroon_up = models.FloatField()  # lower aroon indicator

    def __str__(self):
        name = str(self.ticker) +" - " + str(self.date)
        return name