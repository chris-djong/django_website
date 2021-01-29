import os
import datetime
from core.celery import app
from ..stocks.models import Stock
from iexclass import IexFinanceApi

# Download the latest balance sheet information for the given stocks
@app.task
def download_balance_sheet(iex_tickers):
    today = datetime.date.today()
    iex_finance_api = IexFinanceApi(iex_stocks)


# Celery task that is executed monthly in order to download the stock data
@app.task
def download_stock_analysis():
    iexfinance_tickers = Stock.objects.values_list('iexfinance_ticker')
    print('We would like to download all the stock analysis for the following tickers', iexfinance_tickers)


