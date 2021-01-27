from .models import Stock, Transaction, StockPriceHistory, UserPortfolioHistory, Stockkey, CurrencyHistory, CurrencyTicker
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q
from pandas_datareader import data as pdr
from pandas_datareader._utils import RemoteDataError
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError
import datetime
import os
import sys 

# Obtain the prev weekday, specify how many weekdays in before we want
def get_prev_weekday(date, days=1):
    for _ in range(days):
        date -= datetime.timedelta(days=1)
        while date.weekday() > 4: # Mon-Fri are 0-4
            date -= datetime.timedelta(days=1)
    return date

# Obtain the next weekday, specify how many weekdays in before we want
def get_next_weekday(date, days=1):
    for _ in range(days):
        date += datetime.timedelta(days=1)
        while date.weekday() > 4:
            date += datetime.timedelta(days=1)
    return date

# Function which downloads the currency history object for a given date in case it does not exist yet and retrieves it from the database otherwise
def get_currency_history(currency, date):
    # In case the currency is euro just leave it as is
    if currency.name == "Euro":
        return 1
    else:
        # First try to retrieve the price from the database
        currency_data = CurrencyHistory.objects.filter(currency=currency, date=date)
        # In case we dont have any entries then we start the download
        if currency_data.count() == 0:
            # Try downloading it and saving the object
            try:
                data = pdr.get_data_yahoo(currency.ticker, date).iloc[0]
                to_eur = data["Adj Close"]
                CurrencyHistory.objects.create(currency=currency, date=date, to_eur=to_eur)
                return to_eur
            # In case that does not work simply use the last value
            except:
                time_now = datetime.datetime.today()
                print("Ticker given by", currency)
                print("Error downloading the currency data for now:", time_now)
                print(sys.exc_info()[0])
                print("Returning first previous data found")
                currency_data = CurrencyHistory.objects.latest("date")
                date = currency_data.date
                print("Succesfully found data for date VERIFY THAT THIS DATE IS INDEED CLOSE TO TODAY:", date)
                return currency_data.to_eur
        # If we have downloaded the price already for today just return it 
        else:  
            return currency_data[0].to_eur

# Download the stock for a given date 
def download_stock_date(stock, date):
    try:
        data = pdr.get_data_yahoo(stock.ticker, date).iloc[0]
        if isinstance(stock.ticker, str):
            data['Ticker'] = stock.ticker

        # First delete all the current values in case there are any, so that we get rid of duplicates
        stocks = StockPriceHistory.objects.filter(date=date, ticker=stock)
        stocks.delete()

        # Then obtain the current Currency/EUR price
        to_eur = get_currency_history(stock.currency, date)

        # High low open close
        h = round(data["High"]*to_eur, 2)
        l = round(data["Low"]*to_eur, 2)
        o = round(data["Open"]*to_eur, 2)
        c = round(data["Close"]*to_eur, 2)
        v = round(data["Volume"], 2)

        # And finally save the history
        # Only if all the prices are above 0 (somehow the api return negative prices at a given moment)
        # We have to use stock_id here because we renamed ticker to stock, django can not handle that apparently
        if h>=0 and l >= 0 and c >= 0 and o >= 0 and v >= 0:
            # Then save the new entry
            stock_history = StockPriceHistory.objects.create(ticker=stock, date=date, h=h, l=l, o=o, c=c, v=v)
            stock_history.save()
        else:
            print("Error in stock.tasks.download_stocks_date")
            print("Negative price obtained for", stock, date)
            print("Not saving data")
    # Error handling for different errors 
    except (RemoteDataError):
        print(sys.exc_info()[0])
        print("Please verify whether the ticker %s is correct." % stock.ticker)
        print("RemoteDataError indicates that the yahoo finance api returned that the ticker is not available for free use")
    except (ReadTimeout, ConnectTimeout, ConnectionError):
        print(sys.exc_info()[0])
        print("Request to yahoo finance has timed out for %s." % stock.ticker)
    except (KeyError, ValueError):
        print("Unexpected error:", sys.exc_info()[0])
        print("For %s" % stock.ticker)
        print("This is probably because no data was retrieved due to an exchange closed or similar error.")
        print("We try to get data for date", date)

# Obtain portfolio from database for a given user not the sold ones and combine them immediately in case there are more
def get_portfolio(username, combine=True):
    user = User.objects.get(username=username)
    portfolio = Transaction.objects.filter(user=user, date_sold=None).order_by('label')
    # In case we want to combine stocks, meaning multiple transactions of same stock are merged into one
    if combine:
        # First we have to obtain all the stock name excluding the Watching list, meaning amount of 0
        # Generate portfolio without amount = 0 stocks
        portfolio_non_0 = portfolio.exclude(amount=0)

        # Then obtain the names of these stock
        portfolio_names = portfolio_non_0.values_list('stock', flat=True)

        # Next we have to find all the duplicates
        seen = {}  # dictionary which keeps track of the counts
        duplicates = []  # the ids that have duplicates (it does not matter how many)
        for portfolio_name in portfolio_names:
            if portfolio_name not in seen:
                seen[portfolio_name] = 1
            else:
                if seen[portfolio_name] == 1:
                    duplicates.append(portfolio_name)
                seen[portfolio_name] += 1

        # This is a list with transaction that has to be added at the end to the portfolio as in the following loop all
        # the duplicates will automatically be removed from the portfolio
        transactions_to_add = []
        # Loop through all the duplicates
        for duplicate in duplicates:
            # First obtain all the duplicate transactions
            transactions = portfolio.filter(stock=duplicate).order_by("date_bought")
            # Then remove all the transactions from the portfolio as we add a new one later
            portfolio = portfolio.exclude(stock=duplicate)

            # Then create the necessary variables (all the other ones are not really needed)
            amount = 0
            price_bought = 0
            buy_fees = 0
            sell_fees = 0
            label = ""
            first = True
            transaction_ids = ""
            for transaction in transactions:
                # This automatically removes the Watching transactions as well (maybe fix that we obtain two transactions)
                if label != "Watching" and transaction.amount != 0:
                    amount += transaction.amount
                    price_bought += transaction.price_bought * transaction.amount
                    buy_fees += transaction.buy_fees
                    sell_fees += transaction.sell_fees
                    if first:
                        first = False
                        transaction_ids = str(transaction.id)
                        user = transaction.user
                        stock = transaction.stock
                        # See whether this condition is correct
                        if transaction.label is None:
                            transaction.label = ""
                        label = transaction.label.split("/")
                        date_bought = transaction.date_bought
                        date_sold = transaction.date_sold
                        price_sold = transaction.price_sold
                        buy_fees_constant = transaction.buy_fees_constant
                        buy_fees_linear = transaction.buy_fees_linear
                        sell_fees_constant = transaction.sell_fees_constant
                        sell_fees_linear = transaction.sell_fees_linear
                        lower_alert = transaction.lower_alert
                        upper_alert = transaction.upper_alert
                    else:
                        transaction_ids += "-" + str(transaction.id)
                        if transaction.label is not None:
                            for value in transaction.label.split("/"):
                                if value not in label:
                                    label.append(value)
                        if lower_alert is None:
                            lower_alert = transaction.lower_alert
                        if upper_alert is None:
                            upper_alert = transaction.upper_alert

            # Then average the price bought over the amount to obtain a common entry for all duplicates
            price_bought = price_bought / amount
            # And create the final label
            temp = label
            label = label[0]
            for l in temp:
                label += "/" + l

            # And create the final transaction without saving it to the database
            transaction = Transaction()
            transaction.id = transaction_ids
            transaction.user = user
            transaction.stock = stock
            transaction.amount = amount
            transaction.label = label
            transaction.combined = True
            transaction.price_bought = price_bought
            transaction.buy_fees = buy_fees
            transaction.sell_fees = sell_fees
            transaction.date_bought = date_bought
            transaction.date_sold = date_sold
            transaction.price_sold = price_sold
            transaction.buy_fees_constant = buy_fees_constant
            transaction.buy_fees_linear = buy_fees_linear
            transaction.sell_fees_constant = sell_fees_constant
            transaction.sell_fees_linear = sell_fees_linear
            transaction.lower_alert = lower_alert
            transaction.upper_alert = upper_alert

            transactions_to_add.append(transaction)

        # Call the len function of the queryset once in order to query it from the database
        # We have to add all the transactions togehter because the result_cache variable keeps the last transaction of the queryset
        len(portfolio)
        portfolio._result_cache.extend(transactions_to_add)
    return portfolio


# Obtain all transaction from database for a given user also the sold ones
def get_transactions(username, include_0=False):
    user = User.objects.get(username=username)
    if not include_0:
        transactions = Transaction.objects.filter(user=user).exclude(amount=0).order_by('label')
    else:
        transactions = Transaction.objects.filter(user=user).order_by('label')
    return transactions

def download_stocks_date(stocks, date):
    # We need to convert the input from stock database objects to string tickers for the yahoo finance api
    tickers = ""
    for stock in stocks:
        download_stock_date(stock, date)

# Function that retrieves the price of a given stock at a given date from the database
# It returns both the price and whether the price has been retrieved from the given date or the day before
def get_stock_price_date(stock, date):
    result = {}
    exchange_closed = False
    # Query date from database until we have an actual value
    stock_data = StockPriceHistory.objects.filter(ticker=stock, date=date)
    if stock_data.count() == 0:
        download_stock_date(stock, date)
        stock_data = StockPriceHistory.objects.filter(ticker=stock, date=date)
    # And in case  downloading also did not produce a good result then use a previous value from a previous day
    i = 0 # Safety net for infinite loop error 
    while stock_data.count() == 0:
        date = get_prev_weekday(date)
        # In case we do not have any data for today inside our database it is assumed that the exchange is closed (this assumes that we first download the data before executing the program)
        # Example: This should happen in the morning, if one retrieves the prices before the exchange actually opens
        exchange_closed = True
        stock_data = StockPriceHistory.objects.filter(ticker=stock, date=date)
        # In case we dont have a value for the previous day either try to download it first as well 
        if stock_data.count() == 0:
            download_stock_date(stock, date)
            stock_data = StockPriceHistory.objects.filter(ticker=stock, date=date)
        i += 1
        if i > 9:
            # Error handling
            print("Could not obtain stock data for stock", stock, "and date", date,"verify that the stock object and check whether it is still included in the yahoo finance api")
            return {"high": 0, "low": 0, "open": 0,"close": 0, "exchange_closed": True}

    result["high"] = stock_data.values()[0]["h"]
    result["low"] = stock_data.values()[0]["l"]
    result["open"] = stock_data.values()[0]["o"]
    result["close"] = stock_data.values()[0]["c"]
    result["exchange_closed"] = exchange_closed
    return result

# Function that obtains the relevant context from the database
# or calculates it if required
def get_context(transaction, date=datetime.date.today()):
    today = date
    context = {}

    # Convert transaction.amount from string to float
    transaction.amount = float(transaction.amount)

    # Obtain data for today and extract the relevant variables
    data_today = get_stock_price_date(transaction.stock, today)
    price_today = data_today["close"]
    exchange_closed = data_today["exchange_closed"]

    # Obtain data for yesterday and extract the relevant variables
    yesterday = get_prev_weekday(date)
    data_yesterday = get_stock_price_date(transaction.stock, yesterday)
    price_yesterday = data_yesterday["close"]

    # Obtain currency of stock so that we can automatically check whether the exchange is closed
    to_eur_today = get_currency_history(transaction.stock.currency, today)
    to_eur_yesterday = get_currency_history(transaction.stock.currency, yesterday)

    # This condition is required in the morning, when we obtain data from the yahoo finance server and download it succesfully for the current day
    # but we have actually obtained data from the day before. To fix this we loop through the yesterday data until we obtain a new setpoint
    while (price_yesterday == price_today) or (abs(price_yesterday/to_eur_yesterday - price_today/to_eur_today) < 0.01):
        exchange_closed = True
        # not sure whether this is needed exchange_closed = True
        yesterday = get_prev_weekday(yesterday)
        data_yesterday = get_stock_price_date(transaction.stock, yesterday)
        price_yesterday = data_yesterday["close"]

    # And case we have 2 consecutive dates calculate the context
    daily_change = round(price_today - price_yesterday, 2)
    daily_change_perc = round((daily_change/price_yesterday*100), 1)

    # Calculate the total profit, fees and net amount 
    current_total = round(transaction.amount*price_today, 2)
    initial_total = round(transaction.amount*transaction.price_bought, 2)
    buy_fees = round(transaction.buy_fees, 2)
    sell_fees = round(transaction.sell_fees, 2)
    total_profit = round(current_total - initial_total - buy_fees - sell_fees, 2)
    if initial_total != 0:
        total_profit_perc = round(((total_profit/initial_total)*100), 1)
    else:
        total_profit_perc = 0
    current_total_net = round(current_total-sell_fees, 2)

    # Store all the columns
    context["id"] = transaction.id
    context["ticker"] = transaction.stock.ticker
    context['portfolio'] = transaction.portfolio
    context["name"] = transaction.stock.name
    context["amount"] = transaction.amount
    context["initial_price"] = round(transaction.price_bought, 2)
    context["current_price"] = round(price_today, 2)
    context["daily_change"] = daily_change
    context["daily_change_perc"] = daily_change_perc
    context["current_total_stocks"] = current_total
    context["buy_fees"] = buy_fees
    context["sell_fees"] = sell_fees
    context["exchange_closed"] = exchange_closed
    context["total_profit"] = total_profit
    context["total_profit_perc"] = total_profit_perc
    context["current_total_net"] = current_total_net
    # In case we have a combined transaction simply take the id of the first transaction for the stock ids 
    if transaction.combined:
        context["plot_link"] = os.path.join(os.path.join("/transactions", str(transaction.id.split("-")[0])), "plot")
        context["settings_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "settings_combined")
        context["delete_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "settings_combined")
    else:
        context["plot_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "plot")
        context["settings_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "settings")
        context["delete_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "delete")
    return context


# This function creates a UserPortfolio entry in the database for the given date for the given user
def download_user_portfolio_history(date, user):
    # Obtain all transactions of that user where the buy date is less than or equal to (__lte filter) the desired date
    # Also transaction where the sell date was before should not be considered anymore
    transactions = Transaction.objects.filter(user=user, date_bought__lte=date).filter(Q(date_sold__gte=date)|Q(date_sold=None))
    
    # First delete the value of today so that the it is not included in the following calculations
    user_portfolio_history = UserPortfolioHistory.objects.filter(user=user, date=date)
    user_portfolio_history.delete()

    # Then obtain the latest value to see whether we have free cash flow leftover
    user_portfolio_history_latest = UserPortfolioHistory.objects.filter(user=user).order_by('-date')[0]
    print("Downloading user portfolio history for date", date, "and user", user)
    print("Latest portfolio retrieved from", user_portfolio_history_latest.date)

    total_profit = 0
    total_portfolio = 0
    total_net = 0
    total_cash = user_portfolio_history_latest.cash
    total_invested = 0

    for transaction in transactions:
        stock_data = get_context(transaction.stock, date)
        # In case we have sold the stock today add the profit to the cash variable and remove the invested and net amounts
        if transaction.date_sold == date:
            total_cash += stock_data['amount']*(transaction.price_sold - stock_date['initial_price']) - stock_data['sell_fees'] - stock_data['buy_fees']
        else:
            total_profit += stock_data['total_profit']
            total_invested += stock_data["initial_price"]*stock_data["amount"] + stock_data["sell_fees"] + stock_data["buy_fees"]
            total_net += stock_data['current_total_net']
            total_portfolio += stock_data['current_total_stocks']

    # Calculate portfolio value and store it in database
    user_portfolio_history = UserPortfolioHistory.objects.create(user=user, date=date, cash=total_cash, net=total_net, price=total_portfolio, profit=total_profit, invested=total_invested)
    user_portfolio_history.save()
