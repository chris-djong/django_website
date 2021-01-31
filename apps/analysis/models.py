from django.db import models
from ..stocks.models import Stock

# Simple model to store the API key
class IexApiKey(models.Model):
    sandbox = models.BooleanField(unique=True)
    token = models.CharField(max_length=50)
    messages_available = models.IntegerField()

# Create model to store the KeyStats information
class KeyStats(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()
    avg10Volume = models.IntegerField() 
    avg30Volume = models.IntegerField() 
    day200MovingAvg = models.FloatField()
    day30ChangePercent = models.FloatField()
    day50MovingAvg = models.FloatField()
    day5ChangePercent = models.FloatField()
    dividendYield = models.FloatField()
    employees = models.IntegerField() 
    exDividendDate = models.DateField()
    marketcap = models.FloatField()
    maxChangePercent = models.FloatField()
    month1ChangePercent = models.FloatField()
    month3ChangePercent = models.FloatField()
    month6ChangePercent = models.FloatField()
    nextDividendDate = models.DateField()
    nextEarningsDate = models.DateField()
    peRatio = models.FloatField()
    sharesOutstanding = models.IntegerField()
    ttmDividendRate = models.FloatField()
    ttmEPS = models.FloatField()
    week52change = models.FloatField()
    week52high = models.FloatField()
    week52low = models.FloatField()
    year1ChangePercent = models.FloatField()
    year2ChangePercent = models.FloatField()
    year5ChangePercent = models.FloatField()
    ytdChangePercent = models.FloatField()

    def __str__(self):
      return '%s-%s' % (self.stock, self.date)


  # Create model to store the BalanceSheet information
class BalanceSheet(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()
    commonStock =  models.CharField(max_length=50)
    currentAssets = models.CharField(max_length=50)
    currentCash = models.CharField(max_length=50)
    fiscalDate = models.DateField()
    fiscalQuarter = models.IntegerField()
    fiscalYear = models.IntegerField()
    goodwill = models.CharField(max_length=50)
    intangibleAssets = models.CharField(max_length=50)
    inventory = models.CharField(max_length=50)
    longTermDebt = models.CharField(max_length=50)
    longTermInvestments = models.CharField(max_length=50)
    minorityInterest = models.CharField(max_length=50)
    netTangibleAssets = models.CharField(max_length=50)
    otherAssets = models.CharField(max_length=50)
    otherCurrentAssets = models.CharField(max_length=50)
    propertyPlantEquipment = models.CharField(max_length=50)
    receivables = models.CharField(max_length=50)
    retainedEarnings = models.CharField(max_length=50)
    reportDate = models.DateField()
    shareholderEquity = models.CharField(max_length=50)
    totalAssets = models.CharField(max_length=50)
    totalCurrentLiabilities = models.CharField(max_length=50)
    totalLiabilities = models.CharField(max_length=50)
    treasuryStock = models.CharField(max_length=50)

    def __str__(self):
      return '%s-%s' % (self.stock, self.date)
