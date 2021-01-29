import os
from core.celery import app
from ..stocks.models import Stock
from iexclass import IexFinanceApi

# Download the latest balance sheet information for the given stocks
@app.task
def download_balance_sheet(iex_tickers):
    iex_finance_api = IexFinanceApi(iex_tickers)
    

# Celery task that is executed monthly in order to download the stock data
@app.task


def download_stock_analysis():
    iexfinance_tickers = list(Stock.objects.all().exclude(iexfinance_ticker__isnull=True)values_list('iexfinance_ticker', flat=True))
    download_balance_sheet(iexfinance_tickers)

