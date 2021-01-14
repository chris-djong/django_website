from ..stocks.functions import get_prev_weekday
from .models import IndicatorHistory
import numpy as np

# ToDo: It is sufficient to only execude one query in the task

# Calcuates simple moving average
def calc_sma(stock_data, date, window):
    # Finally obtain the exponential moving average of the given date
    sma = stock_data.rolling(window=window).mean()
    sma_average = sma.loc[date.strftime("%Y-%m-%d")]["c"]

    return sma_average

# Calcuates exponential moving average
def calc_ema(stock_data, date, window):
    # Finally obtain the exponential moving average of the given date
    ewm = stock_data.ewm(span=window, adjust=True).mean()
    exp_average = ewm.loc[date.strftime("%Y-%m-%d")]["c"]

    return exp_average

# Calcuates standart deviation
def calc_std(stock_data, date, window):
    # Finally obtain the exponential moving average of the given date
    std_data = stock_data.rolling(window=window).std()
    std = std_data.loc[date.strftime("%Y-%m-%d")]["c"]

    return std

# Calculate accumulation distribution indicator
def calc_acc_dist(stock_data, date):
    # First obtain stock data of today
    stock = stock_data.iloc[-1]

    # Calculate current money flow volume
    if stock["h"] != stock["l"]: 
        cmfv = ((stock["c"] - stock["l"]) - (stock["h"]- stock["c"]))/(stock["h"] - stock["l"]) * stock["v"]
    else:
        cmfv = 0
    # Obtain previous acc_dist indicator
    date_before = get_prev_weekday(date)
    try:
        indicators_before = IndicatorHistory.objects.filter(stock=stock.id, date=date_before)[0]
        acc_dist_old = indicators_before.acc_dist
    # In case we cant find a previous value set it to 0
    except IndexError:
        acc_dist_old = 0
    # And finally calculate current acc_dist
    acc_dist = acc_dist_old + cmfv
    return acc_dist

# Calculate bollinger bands
def calc_bollinger(stock_data, date):
    # First calculate the mean and std for the given window
    window = 20
    rolling_mean = calc_sma(stock_data, date, window)
    rolling_std = calc_std(stock_data, date, window)

    # Then deduce the bollinger bands from that
    bollinger_upper = rolling_mean + 2*rolling_std
    bollinger_middle = rolling_mean
    bollinger_lower = rolling_mean - 2*rolling_std
    return bollinger_lower, bollinger_middle, bollinger_upper

# Calculate Moving average convergence divergence
def calc_macd(stock_data, date):
    macd = calc_ema(stock_data, date, window=12) - calc_ema(stock_data, date, window=26)
    macd_signal = calc_ema(stock_data, date, window=9)
    return macd, macd_signal


## WIP FROM HERE ON ........
# Calculate stochastic indicator
def calc_stochastic(stock_data):
    stock_data = stock_data.iloc[-14:]

    # Calculate new stochastic indicator
    stochastic = (stock_data.iloc[-1].c - min(stock_data["l"]))/(max(stock_data["h"]) - min(stock_data["l"]))*100
    return stochastic

# Calculate RSI indicator
def calc_rsi(stock_data, date):
    rsi = 0
    # We need a window of 14 but as the daily change is needed we need the 15 value as well
    period = 15
    stock_data = stock_data.iloc[-period:]
    # Then we need to keep track of the up and down movements in order to calculate the average
    up_movements = []
    down_movements = []
    for i in range(1, len(stock_data)):
        daily_change = stock_data.iloc[i].c - stock_data.iloc[i-1].c
        if daily_change >= 0:
            up_movements.append(daily_change)
        else:
            down_movements.append(abs(daily_change))
    avg_up = np.average(up_movements)
    avg_down = np.average(down_movements)
    relative_strength = avg_up/avg_down
    rsi = 100-100/(1+relative_strength)
    return rsi

# Calculate aroon indicator
def calc_aroon(stock, date):
    aroon_down = 0
    aroon_up = 0
    return aroon_down, aroon_up
