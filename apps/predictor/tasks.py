import datetime
from .models import IndicatorHistory
from .functions import calc_acc_dist, calc_bollinger, calc_macd, calc_stochastic, calc_rsi, calc_aroon
from ..stocks.models import Stock, StockPriceHistory
from ..stocks.functions import get_prev_weekday, get_next_weekday
from core.celery import app
import pandas as pd

# This function creates a UserPortfolio entry for all the stocks of a given user since its first buy
# only needed by users/portfolio/download/
@app.task
def download_indicator_history(stock, date):
    # Perform all the SQL queries here so that they are only performed once
    # Max amount of timeframe we need is given by 26 for macd / use +10 for safety factor in case markets are closed for example
    first_date = date
    last_date = date
    window = 26
    for i in range(window+10):
        first_date = get_prev_weekday(first_date)
    stock_data = StockPriceHistory.objects.filter(ticker=stock, date__range=(first_date, last_date))
    if stock_data.count() < 25:
        print("Not enough stock data found for ticker %s", stock)
    else:
        stock_data = stock_data.values()
        stock_data = pd.DataFrame(list(stock_data))
        # Convert to time series
        stock_data = stock_data.set_index("date")
        stock_data = stock_data.sort_index()
        stock_data.index = pd.to_datetime((stock_data.index))

        # Go through all the indicator functions and download them
        acc_dist = calc_acc_dist(stock_data, date)
        bollinger_lower, bollinger_middle, bollinger_upper = calc_bollinger(stock_data, date)
        macd, macd_signal = calc_macd(stock_data, date)
        stochastic = calc_stochastic(stock_data)
        rsi = calc_rsi(stock_data, date)
        aroon_down, aroon_up = calc_aroon(stock_data, date)

        # Delete all previous instances of this date and stock
        indicator_history_data = IndicatorHistory.objects.filter(stock=stock, date=date)
        indicator_history_data.delete()

        # And create a new one
        indicator_history_data = IndicatorHistory.objects.create(stock=stock, date=date, acc_dist=acc_dist, bollinger_upper=bollinger_upper, bollinger_middle=bollinger_middle, bollinger_lower=bollinger_lower, macd=macd, macd_signal=macd_signal, stochastic=stochastic, rsi=rsi, aroon_down=aroon_down, aroon_up=aroon_up)
        indicator_history_data.save()

# Function that download the indicator history for a given stock since a certain day
@app.task
def download_indicator_history_since(stock, date):
    # Get the previous weekday
    day_iterator = get_prev_weekday(date)
    today = datetime.date.today()

    difference_days = (today - day_iterator).days
    while (difference_days >= 0):
        # Download and store indicators
        download_indicator_history(stock, date)

# Downloads indicator history for each stock since a certain day
@app.task
def download_all_indicator_history_since(date):
    # Get the previous weekday
    day_iterator = get_prev_weekday(date)
    today = datetime.date.today()

    difference_days = (today - day_iterator).days
    while (difference_days >= 0):
        print("Days remaining indicator download: %f" % difference_days)
        # Download and store indicators
        download_all_indicator_history(day_iterator)
        day_iterator = get_next_weekday(day_iterator)
        difference_days = (today - day_iterator).days

# Downloads indicator history for all the stocks at a given date
@app.task
def download_all_indicator_history(date):
    stocks = Stock.objects.all()
    for stock in stocks:
        download_indicator_history(stock, date)

# Task for celery download of all indicator history
@app.task
def download_all_indicator_history_today():
    print("Downloading all indicator history today")
    today = datetime.date.today()
    download_all_indicator_history(today)
