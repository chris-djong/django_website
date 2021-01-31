import os
from core.celery import app
from ..stocks.models import Stock
from .iexclass import IexFinanceApi

@app.task
def download_balance_sheet(iex_tickers):
    iex_finance_api = IexFinanceApi(iex_tickers)
    iex_finance_api.query_balance_sheet()

@app.task
def download_key_stats(iex_tickers):
    iex_finance_api = IexFinanceApi(iex_tickers)
    iex_finance_api.query_key_stats()

@app.task
def download_cash_flow(iex_tickers):
    iex_finance_api = IexFinanceApi(iex_tickers)
    iex_finance_api.query_cash_flow()

@app.task
def download_income_statement(iex_tickers):
    iex_finance_api = IexFinanceApi(iex_tickers)
    iex_finance_api.query_income_statement()   

# Celery task that is executed monthly in order to download the stock data
@app.task
def download_stock_analysis():
    iexfinance_tickers = list(Stock.objects.all().exclude(iexfinance_ticker__isnull=True).values_list('iexfinance_ticker', flat=True))
    download_balance_sheet(iexfinance_tickers)
    download_key_stats(iexfinance_tickers)
    download_cash_flow(iexfinance_tickers)
    download_income_statement(iexfinance_tickers)



