from django.db import models
from ..stocks.models import Stock

# Simple model to store the API key
class IexApiKey(models.Model):
    sandbox = models.BooleanField(unique=True)
    token = models.CharField(max_length=50)
    messages_available = models.IntegerField()

# Create model to store the KeyStats information
class KeyStats(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)
    date = models.DateField(null=True)
    avg10Volume = models.IntegerField(null=True) 
    avg30Volume = models.IntegerField(null=True) 
    day200MovingAvg = models.FloatField(null=True)
    day30ChangePercent = models.FloatField(null=True)
    day50MovingAvg = models.FloatField(null=True)
    day5ChangePercent = models.FloatField(null=True)
    dividendYield = models.FloatField(null=True)
    employees = models.CharField(max_length=50, null=True) 
    exDividendDate = models.DateField(null=True)
    marketcap = models.CharField(max_length=50, null=True)
    maxChangePercent = models.FloatField(null=True)
    month1ChangePercent = models.FloatField(null=True)
    month3ChangePercent = models.FloatField(null=True)
    month6ChangePercent = models.FloatField(null=True)
    nextDividendDate = models.DateField(null=True)
    nextEarningsDate = models.DateField(null=True)
    peRatio = models.FloatField(null=True)
    sharesOutstanding = models.CharField(max_length=50, null=True)
    ttmDividendRate = models.FloatField(null=True)
    ttmEPS = models.FloatField(null=True)
    week52change = models.FloatField(null=True)
    week52high = models.FloatField(null=True)
    week52low = models.FloatField(null=True)
    year1ChangePercent = models.FloatField(null=True)
    year2ChangePercent = models.FloatField(null=True)
    year5ChangePercent = models.FloatField(null=True)
    ytdChangePercent = models.FloatField(null=True)

    def __str__(self):
      return '%s-%s' % (self.stock, self.date)


  # Create model to store the BalanceSheet information
class BalanceSheet(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)
    date = models.DateField(null=True)
    commonStock =  models.CharField(max_length=50, null=True)
    currentAssets = models.CharField(max_length=50, null=True)
    currentCash = models.CharField(max_length=50, null=True)
    fiscalDate = models.DateField(null=True)
    fiscalQuarter = models.IntegerField(null=True)
    fiscalYear = models.IntegerField(null=True)
    goodwill = models.CharField(max_length=50, null=True)
    intangibleAssets = models.CharField(max_length=50, null=True)
    inventory = models.CharField(max_length=50, null=True)
    longTermDebt = models.CharField(max_length=50, null=True)
    longTermInvestments = models.CharField(max_length=50, null=True)
    minorityInterest = models.CharField(max_length=50, null=True)
    netTangibleAssets = models.CharField(max_length=50, null=True)
    otherAssets = models.CharField(max_length=50, null=True)
    otherCurrentAssets = models.CharField(max_length=50, null=True)
    propertyPlantEquipment = models.CharField(max_length=50, null=True)
    receivables = models.CharField(max_length=50, null=True)
    retainedEarnings = models.CharField(max_length=50, null=True)
    reportDate = models.DateField(null=True)
    shareholderEquity = models.CharField(max_length=50, null=True)
    totalAssets = models.CharField(max_length=50, null=True)
    totalCurrentLiabilities = models.CharField(max_length=50, null=True)
    totalLiabilities = models.CharField(max_length=50, null=True)
    treasuryStock = models.CharField(max_length=50, null=True)

    def __str__(self):
      return '%s-%s' % (self.stock, self.date)


class CashFlow(models.Model):
    stock                    = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)
    date                     = models.DateField(null=True)
    capitalExpenditures      = models.CharField(max_length=50, null=True)
    cashFlow                 = models.CharField(max_length=50, null=True)
    cashFlowFinancing        = models.CharField(max_length=50, null=True)
    depreciation             = models.CharField(max_length=50, null=True)
    fiscalDate               = models.DateField(null=True)
    fiscalQuarter            = models.IntegerField(null=True)
    fiscalYear               = models.IntegerField(null=True)
    netIncome                = models.CharField(max_length=50, null=True)
    reportDate               = models.DateField(null=True)
    totalInvestingCashFlows  = models.CharField(max_length=50, null=True)

    def __str__(self):
        return '%s-%s' % (self.stock, self.date)

class IncomeStatement(models.Model):
    stock                  = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)
    date                   = models.DateField(null=True)
    costOfRevenue          = models.CharField(max_length=50, null=True)
    ebit                   = models.CharField(max_length=50, null=True)
    filingType             = models.CharField(max_length=50, null=True)
    fiscalDate             = models.DateField(null=True)
    fiscalQuarter          = models.IntegerField(null=True)
    fiscalYear             = models.IntegerField(null=True)
    grossProfit            = models.CharField(max_length=50, null=True)
    incomeTax              = models.CharField(max_length=50, null=True)
    interestIncome         = models.CharField(max_length=50, null=True)
    minorityInterest       = models.CharField(max_length=50, null=True)
    netIncome              = models.CharField(max_length=50, null=True)
    netIncomeBasic         = models.CharField(max_length=50, null=True)
    operatingExpense       = models.CharField(max_length=50, null=True)
    operatingIncome        = models.CharField(max_length=50, null=True)
    otherIncomeExpenseNet  = models.CharField(max_length=50, null=True)
    pretaxIncome           = models.CharField(max_length=50, null=True)
    reportDate             = models.DateField(null=True)
    researchAndDevelopment = models.CharField(max_length=50, null=True)
    sellingGeneralAndAdmin = models.CharField(max_length=50, null=True)
    totalRevenue           = models.CharField(max_length=50, null=True)

    def __str__(self):
        return '%s-%s' % (self.stock, self.date)
