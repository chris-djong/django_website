from django.shortcuts import render
from ..stocks.functions import get_portfolio, get_stock_price_date
from .models import IndicatorHistory
import datetime

# View that shows indicators in same tabular form as transaction overview
def predictor_overview_view(request, *args, **kwargs):
    # Obtain all the relevant transactions
    username = request.user.username
    transactions = get_portfolio(username)
    today = datetime.datetime.today()

    # Queryset to store indicator data for each transaction
    queryset = {}
    # Retrieve the indicator data for each of them
    for transaction in transactions:
        indicator_data = IndicatorHistory.objects.filter(stock=transaction.stock, date=today)
        if indicator_data.count() > 0 :
            data_today = get_stock_price_date(transaction.stock, today)
            price_today = data_today["close"]
            indicator_results = {}
            indicator_data = indicator_data[0]
            indicator_results['acc_dist'] = round(indicator_data.acc_dist, 2)
            indicator_results['bollinger'] = round(((price_today - indicator_data.bollinger_middle)/(indicator_data.bollinger_upper - indicator_data.bollinger_lower)), 2)
            indicator_results['macd_final'] = round(indicator_data.macd, 2)
            indicator_results['stochastic'] = round(indicator_data.stochastic, 2)
            indicator_results['rsi'] = round(indicator_data.rsi, 2)
            indicator_results['aroon'] = 0
            queryset[transaction.stock.ticker] = indicator_results

    context = {"queryset": queryset, }
    return render(request, "predictor_overview.html", context)


