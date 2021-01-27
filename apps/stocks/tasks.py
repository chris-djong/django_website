from .models import Transaction, Stock, StockPriceHistory, UserPortfolioHistory
from .functions import get_context, get_transactions, get_portfolio, download_stocks_date, download_stock_date, get_next_weekday, get_prev_weekday, get_stock_price_date, download_user_portfolio_history
from ..mail_relay.tasks import send_mail
import datetime
from django.contrib.auth.models import User
from core.celery import app
import numpy as np

# Functions that sends alert for either upper or lower alert
def send_alert_mail(user_mail, transaction, price_today, alert_value):
    # First deduce whether we have an upper or a lower alert
    if price_today >= alert_value:
        subject = "Upper alert %s" % (transaction.stock)
        message = "This is an automatic alert mail for %s\n\nThe price has exceeded your upper alert!\n\nCurrent price: %f\nAlert level: %f" % (transaction.stock, price_today, alert_value)
    elif price_today <= alert_value:
        subject = "Lower alert %s" % (transaction.stock)
        message = "This is an automatic alert mail for %s\n\nThe price has fallen past you lower alert!\n\nCurrent price: %f\nAlert level: %f" % (transaction.stock, price_today, alert_value)
    send_mail.delay("alert@dejong.lu", [user_mail], subject, message)


# Function that merges multiple transactions that have the same ticker and sells the stocks in case we have both a buy and a sell 
@app.task
def merge_transactions(username):
    portfolio = get_portfolio(username, combine=False)
    portfolio_names = portfolio.values_list('stock', flat=True)

    # First find duplicates
    seen = {}  # dictionary which keeps track of the counts
    duplicates = []  # the ids that have duplicates (it does not matter how many)
    for portfolio_name in portfolio_names:
        if portfolio_name not in seen:
            seen[portfolio_name] = 1
        else:
            if seen[portfolio_name] == 1:
                duplicates.append(portfolio_name)
            seen[portfolio_name] += 1
    # Loop through all the duplicates
    for duplicate in duplicates:
        # Obtain all the duplicate transactions
        transactions = portfolio.filter(stock=duplicate).order_by("date_bought")
        # Sort them whether they are buy or sell and find out what the total is
        buys = []
        sells = []
        total = 0
        for transaction in transactions:
            total += transaction.amount
            if transaction.amount >= 0: 
                buys.append(transaction)
            else: 
                sells.append(transaction)
        # In case the total is positive we have to keep a buy transaction, which means sell all the sells 
        if total >= 0:
            for sell in sells:
                # Until we have sold all off the stock of the sell transaction we keep looping
                left_to_sell = -sell.amount
                buy_index = 0  # index to loop through buy stocks / this should always work out as total > 0 / infinite loop  otherwise
                while left_to_sell != 0:
                    buy = buys[buy_index]
                    
                    # In case we have more to sell than the current buy then just sell the whole buy   
                    if left_to_sell >= buy.amount:
                        buy.sell_fees_linear = sell.buy_fees_linear
                        buy.sell_fees_constant = sell.buy_fees_constant
                        buy.date_sold = sell.date_bought
                        buy.price_sold = sell.price_bought
                        buy.sell_fees = sell.buy_fees
                        left_to_sell -= buy.amount
                        buy.save()
                        buy_index += 1
                    # Otherwise in case we have more bought than we can sell we have to create 2 transactions
                    else:
                        # First reduce the amount of the buy transaction by the sold amount
                        buy.amount -= left_to_sell 
                        buy.save()

                        # And then create a new transaction which is sold
                        buy.pk = None
                        buy.amount = left_to_sell
                        left_to_sell -= buy.amount
                        buy.date_sold = sell.date_bought
                        buy.price_sold = sell.price_bought
                        buy.sell_fees_constant = sell.buy_fees_constant
                        buy.sell_fees_linear = sell.buy_fees_linear
                        buy.sell_fees = sell.buy_fees
                        buy.save()
                if left_to_sell == 0:
                    sell.delete()
        # In case the total is negative we have to keep a sell transaction, which means buy all the buys 
        else:
            for buy in buys:
                # Until we have bought all off the stock of the buy transaction we keep looping
                left_to_buy = buy.amount
                sell_index = 0  # index to loop through sell stocks / this should always work out as total < 0 / infinite loop otherwise
                while left_to_buy != 0:
                    sell = sells[sell_index]
                    # In case we have more to buy that the current sell then just buy the whole sell   
                    if left_to_buy >= -sell.amount:
                        sell.date_sold = sell.date_bought
                        sell.price_sold = sell.price_bought
                        sell.sell_fees_constant = sell.buy_fees_constant
                        sell.sell_fees_linear = sell.buy_fees_linear
                        sell.sell_fees = sell.buy_fees
                        sell.date_bought = buy.date_bought
                        sell.price_bought = buy.price_bought
                        sell.buy_fees_linear = buy.buy_fees_linear
                        sell.buy_fees_constant = buy.buy_fees_constant
                        sell.buy_fees = buy.buy_fees
                        left_to_buy -= sell.amount
                        sell.save()
                        sell_index += 1
                    # Otherwise in case we have more sold than we can buy we have to create 2 transactions
                    else:
                        # First reduce the amount of the sell transaction by the buy amount
                        sell.amount += left_to_buy 
                        sell.save()

                        # And then create a new transaction which is bought
                        sell.pk = None
                        sell.amount = left_to_buy
                        left_to_buy -= sell.amount
                        sell.date_sold = sell.date_bought
                        sell.price_sold = sell.price_bought
                        sell.sell_fees_constant = sell.buy_fees_constant
                        sell.sell_fees_linear = sell.buy_fees_linear
                        sell.sell_fees = sell.buy_fees
                        sell.date_bought = buy.date_bought
                        sell.price_bought = buy.price_bought
                        sell.buy_fees_linear = buy.buy_fees_linear
                        sell.buy_fees_constant = buy.buy_fees_constant
                        sell.buy_fees = buy.buy_fees
                        sell.save()
                if left_to_buy == 0:
                    buy.delete()



# Download stock data for a specific day and a specific stock
# This function calls the yahoo finance API and downloads stock data since the given date
# Data is only stored in the database in case no previous record has been stored or in case the record has been stored in the last week
@app.task
def download_stock_since(day, month, year, stock):
    today = datetime.date.today()
    # Verify for no input of user
    if year != "" and day != "" and month != "":
        # Transform user input to date variable
        day_iterator = datetime.date(year=int(year), day=int(day), month=int(month))

        # Go to a weekday
        day_iterator = get_next_weekday(day_iterator)
        day_iterator = get_prev_weekday(day_iterator)

        # Calculate the difference in days from today
        difference_days = (today - day_iterator).days

        while (difference_days >= 0):
            download_stock_date(stock, day_iterator)

            # Move to the next day
            day_iterator = get_next_weekday(day_iterator)
            difference_days = (today - day_iterator).days

# Download stock data for specific stocks
# The input is a date since when we want to download the stocks and a list containing all the stocks
@app.task
def download_stocks_since(day, month, year, stocks):
    today = datetime.date.today()
    # Verify for no input of user
    if year != "" and day != "" and month != "":
        # Transform user input to date variable
        day_iterator = datetime.date(year=int(year), day=int(day), month=int(month))

        # Go to a weekday
        day_iterator = get_next_weekday(day_iterator)
        day_iterator = get_prev_weekday(day_iterator)

        # Calculate the difference in days from today
        difference_days = (today - day_iterator).days

        while (difference_days >= 0):
            # Download the stock data for that day
            download_stocks_date(stocks, day_iterator)

            # Move to the next day
            day_iterator = get_next_weekday(day_iterator)
            difference_days = (today - day_iterator).days



# Download stock data for all stocks in Database
# This functions downloads data for all the stocks
@app.task
def download_all_stocks_since(day, month, year):
    # Verify for no input of user
    if year != "" and day != "" and month != "":
        # We want to download all the stocks
        stocks = Stock.objects.all()
        download_stocks_since(day, month, year, stocks)

# Function that downloads the stocks of each current user
# This function will be executed by the celerybeat process hourly
@app.task
def download_all_stocks_today():
    today = datetime.date.today()
    stocks = Stock.objects.all()
    download_stocks_date(stocks, today)
    process_all_download_data()

# This function creates a UserPortfolio entry for all the stocks of a given user since its first buy
# only needed by users/portfolio/download/
@app.task
def download_user_portfolio_history_since(username, date):
    # Loop through each day until today
    # We first have to convert our datetime string to a datetime object
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date.split("T")[0])
    day_iterator = get_prev_weekday(date)

    today = datetime.date.today()

    difference_days = (today - day_iterator).days
    while (difference_days >= 0):
        # Download and store user portfolio information
        user = User.objects.get(username=username)
        download_user_portfolio_history(day_iterator, user)

        # And obtain values for new iteration
        day_iterator = get_next_weekday(day_iterator)
        difference_days = (today - day_iterator).days




# This function creates a UserPortfolio entry for all the stocks of a given user since its first buy
# only needed by users/portfolio/download/
@app.task
def download_all_user_portfolio_history(username):
    # First obtain all transaction sorted by buy date
    transactions = get_transactions(username, include_0=False)
    transactions = transactions.order_by('date_bought')

    # Then use the first transaction to initialise the prices
    initial_date = transactions[0].date_bought - datetime.timedelta(1)

    download_user_portfolio_history_since(username, initial_date)


# Function that verifies the current stock prices, updates the sell fees and verifies whether an alert has to be send
def process_download_data(username):
    # Obtain current user
    user = User.objects.get(username=username)
    
    portfolio = get_portfolio(username, combine=False)

    for transaction in portfolio:
        transaction_context = get_context(transaction)

        # Check whether an alert has been exceeded
        price_today = transaction_context["current_price"]
        price_yesterday = price_today - transaction_context["daily_change"]
        # Lower alert
        if transaction.lower_alert is not None:
            if price_today < transaction.lower_alert and price_yesterday >= transaction.lower_alert:
                send_alert_mail(user.email, transaction, price_today, transaction.lower_alert)
                transaction.lower_alert = None
        # Upper alert
        if transaction.upper_alert is not None:
            if price_today > transaction.upper_alert and price_yesterday <= transaction.upper_alert:
                send_alert_mail(user.email, transaction, price_today, transaction.upper_alert)
                transaction.upper_alert = None

        # Set the sell fees
        transaction.sell_fees = transaction.sell_fees_constant + transaction.sell_fees_linear*transaction_context["amount"]*transaction_context["current_price"]

        # And save the transaction
        transaction.save()

    date = get_prev_weekday(datetime.date.today(), days=4)
    download_user_portfolio_history_since(username, date)


# Function that loops through all the users to process the download data such as user information models, sell fees and alerts
# This function is required because otherwise we have to loop through duplicate transactions
def process_all_download_data():
    users = User.objects.all()
    for user in users:
        username = user.username
        process_download_data(username)


