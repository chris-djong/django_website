import datetime
import os
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .functions import get_transactions, get_portfolio, get_historical_data, get_prev_weekday, get_context, obtain_start_date, get_currency_history
from .tasks import download_all_stocks_since, download_stock_since, download_all_user_portfolio_history, download_user_portfolio_history_since, merge_transactions, download_all_stocks_today
from .forms import TransactionCreationForm, TransactionSettingsForm, TransactionSellForm, StockCreationForm, StockSettingsForm, TransactionWatchForm, UserForm, DateForm, DateRangeForm
from .models import Transaction, StockPriceHistory, UserPortfolioHistory, Stock
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce
import time
import matplotlib as mplt
import pandas as pd 
import numpy as np
from ..newsapi.tasks import download_articles_since

# Create your vigws here.
@login_required(login_url="login")
def transaction_overview_view(request, *args, **kwargs):
    username = request.user.username
    merge_transactions(username)
    portfolio = get_portfolio(username)

    # List with dictionaries for final context to template 
    # queryset = {"label1": [transaction1, transaction2, transaction3], "label2: [transaction1, transaction2, transaction3]"} 
    querysets = {}    # querysets = {"portfolio1": queryset1, "portfolio2": queryset2}
    # Also create the datasets for the diversification chart
    diversification_chart_dict = {}

    for transaction in portfolio:
        ## Calculate and store relevant data
        transaction_context = get_context(transaction)
        
        # Check whether we created the portfolio already
        portfolio = transaction_context["portfolio"]
        if portfolio not in querysets:
            querysets[portfolio] = {}
           
        # Set label to string for error handling
        if (transaction.label is None):
            transaction.label = ""

        # Now we have to split the labels which are saved using / as seperator 
        labels = transaction.label.split("/")
        # Loop through the labels
        for i in range(len(labels)):
            label = labels[i]
            # We only add the first label to the queryset for generation of the overview
            if i == 0:
                if label in querysets[portfolio]:
                    querysets[portfolio][label].append(transaction_context)
                else:
                    querysets[portfolio][label] = [transaction_context, ]
            # All the other labels are added to the diversification chart in case they are not part of the watching
            if label != "Watching":
                if label in diversification_chart_dict:
                    diversification_chart_dict[label] += transaction_context["amount"]*transaction_context["current_price"]
                else:
                    diversification_chart_dict[label] = transaction_context["amount"]*transaction_context["current_price"] 
 
    # Add watching queryset by default in case it is not there yet
    if "Watching" not in querysets.keys():
        querysets["Watching"] = {}

    # Now convert the diversification_chart_dict to values comprehended by chart.js
    diversification_chart_labels = list(diversification_chart_dict.keys())
    diversification_chart_values = list(diversification_chart_dict.values())
    diversification_chart_colors = ["#61829F"]*len(diversification_chart_values)
    # Create data for portfolio hisotry plotting
    user_portfolio_history = UserPortfolioHistory.objects.filter(user=request.user)
    user_portfolio_history = user_portfolio_history.order_by('date').reverse()

    # Create plotting data
    portfolio_plot_labels = []
    portfolio_plot_data = []
    portfolio_plot_profit = []
    for data in user_portfolio_history:
        portfolio_plot_labels.append(data.date.strftime("%Y-%m-%d"))
        portfolio_plot_data.append(data.price)
        portfolio_plot_profit.append(data.profit)
    
    # Obtain daily change
    index_error = False
    try:
        daily_change = round((portfolio_plot_data[0] - portfolio_plot_data[1]), 2)
        daily_change_perc = round((daily_change/portfolio_plot_data[0]*100), 2)
    except (IndexError, ZeroDivisionError) as e:
        index_error = True

    # Find out whether all of the exchanges are still closed
    daily_from_today = True
    if index_error:
        daily_from_today = False
        try:
            daily_change = round((portfolio_plot_data[0] - portfolio_plot_data[1]), 2)
            daily_change_perc = round((daily_change/portfolio_plot_data[0]*100), 2)
        except (IndexError, ZeroDivisionError):
            daily_change = 0
            daily_change_perc = 0


    try:
        initial_total_stocks = round(user_portfolio_history[0].invested, 2)
        current_total_stocks = round(user_portfolio_history[0].price, 2)
        current_total_profit = round(user_portfolio_history[0].profit, 2)
        current_total_net = round(user_portfolio_history[0].net, 2)
        current_total_cash = round(user_portfolio_history[0].cash, 2)
    except IndexError:
        print("Index error for user portfolio history")
        initial_total_stocks = 0
        current_total_stocks = 0
        current_total_profit = 0
        current_total_net = 0
        current_total_cash = 0
    # And calculate the percentage
    if initial_total_stocks == 0:
        current_total_profit_perc = 0
    else:
        current_total_profit_perc = round(current_total_profit/initial_total_stocks*100, 2)

    # Add all the required variables to the context for processing by the template
    my_context = {"daily_change": daily_change, "daily_change_perc": daily_change_perc, "querysets": querysets, "portfolio_plot_labels": portfolio_plot_labels, "portfolio_plot_data": portfolio_plot_data, "portfolio_plot_profit": portfolio_plot_profit, "current_total_net": current_total_net, "initial_total_stocks": initial_total_stocks, "current_total": current_total_stocks,"current_total_profit":current_total_profit, "current_total_profit_perc":current_total_profit_perc, "diversification_chart_labels": diversification_chart_labels, "diversification_chart_values":diversification_chart_values, "diversification_chart_colors": diversification_chart_colors, "daily_from_today": daily_from_today, "current_total_cash": current_total_cash}
    return render(request, "transaction_overview.html", my_context)

# View for creation of new stocks
@login_required(login_url="login")
def transaction_creation_view(request, portfolio, *args, **kwargs):
    if request.method == "GET":
        today = datetime.datetime.today()
        if portfolio == 'Watching':
            my_form = TransactionCreationForm(initial= {"date_bought": today, "amount": 0, "portfolio": portfolio})
        else:
            my_form = TransactionCreationForm(initial= {"date_bought": today, "portfolio": portfolio})
    elif request.method == "POST":
        my_form = TransactionCreationForm(request.POST)
        if my_form.is_valid():
            # First save the data but do not commit it yet 
            transaction = my_form.save(commit=False)
            transaction.user = request.user

            if transaction.portfolio is None:
                transaction.portfolio = "Portfolio"

            # In case the user did not put in a price_bought date
            if transaction.price_bought is None:
                found = False
                download_date = transaction.date_bought
                if download_date.weekday() >= 5:
                    download_date = get_prev_weekday(download_date)

                # Safety measure for infinite loop
                i = 0
                while not found:
                    i += 1
                    if i == 5:
                        data_bought = {"Close": -12345}
                        found = True
                        continue

                    data_bought, found = get_historical_data(transaction.stock.ticker, download_date)
                    download_date = get_prev_weekday(download_date)

                # Then obtain the current Currency/EUR price
                to_eur = get_currency_history(transaction.stock, download_date)
                transaction.price_bought = round(data_bought["Close"]*to_eur, 2)

            # Calculate the buy fees based on constant and linear term
            transaction.buy_fees = transaction.buy_fees_constant + transaction.buy_fees_linear*transaction.price_bought*transaction.amount

            # Same for sell fees, however the actual value is here calculated in download_stock function
            transaction.sell_fees = 0 # actual sell_fees calculation performed later on in download_stock function

            # Save data and download stock data for the last 5 days
            transaction.save()

            download_date = get_prev_weekday(datetime.date.today(), days=5)
            download_stock_since(day=download_date.day, month=download_date.month, year=download_date.year, stock=transaction.stock)
            download_articles_since.delay(transaction.id, download_date)

            download_date = get_prev_weekday(transaction.date_bought, days=4)
            download_user_portfolio_history_since.delay(username=request.user.username, date=download_date)
            return redirect("portfolio")

        else:
            # Throw an error?
            raise Http404("TransactionCreationForm not valid.")

    context = {"form": my_form}
    return render(request, "transaction_create.html", context)

# Confirmation view for deletion of stocks
@login_required(login_url="login")
def transaction_delete_view(request, id, *args, **kwargs):
    transaction = get_object_or_404(Transaction, id=id)
    if transaction.user == request.user:
        if request.method == "POST":
            transaction.delete()
            download_user_portfolio_history_since.delay(username=request.user.username, date=transaction.date_bought)
            return redirect("/portfolio")
        else:
            context = {"object":transaction}
            return render(request, "transaction_delete.html", context)
    else:
        raise Http404("No transaction matches the given query.")

# Combined settings overview in case stocks are merged
@login_required(login_url="login")
def transaction_settings_combined_view(request, ids):
    transactions = Transaction.objects.filter(id__in=ids.split("-"))
    # List with dictionaries for final context
    queryset = {"": []}     # queryset = {"label1": [transaction1, transaction2, transaction3], "label2: [transaction1, transaction2, transaction3]"} 
    # Also create the datasets for the diversification chart
    for transaction in transactions:
        ## Calculate and store relevant data
        transaction_context = get_context(transaction)
        queryset[""].append(transaction_context)
    context = {"queryset": queryset}
    return render(request, "transaction_settings_combined.html", context)


# Confirmation view for deletion of stocks
@login_required(login_url="login")
def transaction_sell_view(request, id, *args, **kwargs):
    transaction = get_object_or_404(Transaction, id=id)
    # Verify whether user is allowed to modify the given transaction
    if transaction.user == request.user:
        if request.method == "GET":
            transaction_sell_form = TransactionSellForm()
        elif request.method == "POST":
            # Put all the data that the user entered into a form in order to overwrite it onto the actual transaction later on 
            transaction_sell_form = TransactionSellForm(request.POST)
            if transaction_sell_form.is_valid():
                # Obtain the actual transaction to overwrite the data too 
                transaction = get_object_or_404(Transaction, id=id)
                # If we did not enter a valid Date just use today
                if transaction_sell_form.data["date_sold_year"] == "":
                    date = datetime.date.today()
                else:
                    date = datetime.date(int(transaction_sell_form.data['date_sold_year']), int(transaction_sell_form.data['date_sold_month']), int(transaction_sell_form.data['date_sold_day']))
                # Make sure it is a weekday
                if date.weekday() >= 5:
                    date = get_prev_weekday(date)
                transaction.date_sold = date

                # If we did not add a price sold use the Adj Close price of the date sold
                if transaction_sell_form.data["price_sold"] is None:
                    # ToDo: Make function out of this, same for all examples in functions.py
                    found = False
                    date = transaction.date_sold
                    # Safety mesaure for infinite loop
                    i = 0
                    while not found:
                        i += 1
                        if i == 100:
                            data_sold = {"Adj Close": -123082}
                            found = True
                        data_sold, found = get_historical_data(transaction.stock.ticker, date)
                        date = get_prev_weekday(date)

                    transaction.price_sold = data_sold["Adj Close"]
                else:
                    transaction.price_sold = transaction_sell_form.data["price_sold"]
                transaction.save()
                return redirect("portfolio")
            else:
                raise Http404("Transaction sell form not valid.")
        context = {"form": transaction_sell_form, "stock": transaction.stock}
        return render(request, "transaction_sell.html", context)
    else:
        raise Http404("No transaction matches the given query.")

@login_required(login_url="login")
def user_portfolio_download_view(request):
    if request.user.username == "chris":
        # Show form in case we came her using a GET request
        if request.method == "GET":
            user_form = UserForm()
            context = {"form": user_form}
            return render(request, "request_user.html", context)
        elif request.method == "POST":
            user_form = UserForm(request.POST)
            username = User.objects.filter(id=user_form.data["user"])[0].username
            download_all_user_portfolio_history.delay(username)
            return redirect("portfolio")
    else:
        raise Http404("Page not found")

@login_required(login_url="login")
def stock_download_since_view(request):
    if request.user.username == "chris":
        # Show form in case we came here using a GET request
        if request.method == "GET":
            date_form = DateForm()
            context = {"form": date_form}
            return render(request, "request_date.html", context)
        elif request.method == "POST":
            # Obtain data entered by user
            date_form = DateForm(request.POST)
            day = date_form.data['date_day']
            month = date_form.data['date_month']
            year = date_form.data['date_year']

            # Then send all the stocks to the celery worker
            download_all_stocks_since.delay(day=day, month=month, year=year)

            # And redirect to the portfolio
            return redirect("/portfolio")

    else: # in case its not tock_e
        raise Http404("Page not found")


# In order to download all data from today (execute the celery task)
@login_required(login_url="login")
def stock_download_today_view(request):
    if request.user.username == "chris":
        download_all_stocks_today.delay()
        # And redirect to the portfolio
        return  redirect("/portfolio")

    else: # in case its not me
        raise Http404("Page not found")


# Change the news ticker of a given stock
@login_required(login_url="login")
def stock_change_article_ticker_view(request, id):
    # First obtain stock
    stock = get_object_or_404(Stock, id=id)

    # First retrieve the corresponding settings from the database
    if request.method == "GET":
        settings_form = StockSettingsForm(initial={"ticker": stock.ticker, "article_ticker": stock.article_ticker, "plot_ticker": stock.plot_ticker, "name": stock.name, "currency":stock.currency})
    elif request.method == "POST":
        settings_form = StockSettingsForm(request.POST)
        if settings_form.is_valid():
            if settings_form.data["article_ticker"] != "":
                # If the form is valid get the relevant stock
                stock = get_object_or_404(Stock, id=id)

                # And update the settings
                stock.article_ticker = settings_form.data["article_ticker"]

                # Finally save them
                stock.save()

            return redirect("news")
        else:
            # Throw an error?
            raise Http404(settings_form.errors)
        
    context = {"form": settings_form, 'name': stock.name}
    return render(request, "stock_change_news_ticker.html", context)

# View that manages and stores settings for history view (here dates can all be changed and alerts have been removed) 
@login_required(login_url="login")
def transaction_settings_history_view(request, id):
    transaction = get_object_or_404(Transaction, id=id)

    if transaction.user == request.user:
        # First retrieve the corresponding settings from the database
        if request.method == "GET":
            settings_form = TransactionSettingsForm(initial={"stock":transaction.stock,"amount": transaction.amount, "label":transaction.label, "price_bought":transaction.price_bought, "buy_fees": transaction.buy_fees, "sell_fees": transaction.sell_fees, "buy_fees_constant": transaction.buy_fees_constant, "sell_fees_constant": transaction.sell_fees_constant, "buy_fees_linear": transaction.buy_fees_linear, "sell_fees_linear": transaction.sell_fees_linear, "lower_alert":transaction.lower_alert, "upper_alert":transaction.upper_alert, "date_bought": transaction.date_bought, "date_sold":transaction.date_sold, "price_sold": transaction.price_sold})
        elif request.method == "POST":
            settings_form = TransactionSettingsForm(request.POST)
            if settings_form.is_valid():
                # If the form is valid get the relevant stock
                transaction = get_object_or_404(Transaction, id=id)
                # And update the settings
                transaction.stock = get_object_or_404(Stock, id=settings_form.data['stock'])
                transaction.amount = settings_form.data['amount']
                date = datetime.date(int(settings_form.data['date_bought_year']), int(settings_form.data['date_bought_month']), int(settings_form.data['date_bought_day']))
                if date.weekday() >= 5:
                    date = get_prev_weekday(date)
                transaction.date_bought = date
                transaction.price_bought = float(settings_form.data["price_bought"])

                if settings_form.data['date_sold_year'] != '' and settings_form.data['date_sold_month'] != "" and settings_form.data['date_sold_year'] != "":
                    date = datetime.date(int(settings_form.data['date_sold_year']), int(settings_form.data['date_sold_month']), int(settings_form.data['date_sold_day']))
                    if date.weekday() >= 5:
                        date = get_prev_weekday(date)
                    transaction.date_sold = date
                if settings_form.data["price_sold"] != '':
                    transaction.price_sold = float(settings_form.data["price_sold"])

                # Calculate buy fees
                transaction.buy_fees_linear = settings_form.data["buy_fees_linear"]
                transaction.buy_fees_constant = settings_form.data["buy_fees_constant"]
                transaction.buy_fees = float(transaction.price_bought)*float(transaction.amount)*float(transaction.buy_fees_linear) + float(transaction.buy_fees_constant)

                # And the sell fees
                transaction_context = get_context(transaction)
                transaction.sell_fees_linear = settings_form.data["sell_fees_linear"]
                transaction.sell_fees_constant = settings_form.data["sell_fees_constant"]
                transaction.sell_fees = float(transaction.sell_fees_constant) + float(transaction.sell_fees_linear)*transaction_context["amount"]*transaction_context["current_price"]

                # Finally save them
                transaction.save()

                download_user_portfolio_history_since.delay(username=request.user.username, date=transaction.date_bought)
                return redirect("history")
            else:
                # Throw an error?
                raise Http404("Transaction settings form not valid.")
            
        context = {"form": settings_form}
        return render(request, "transaction_settings_history.html", context)
    else:
        raise Http404("No Stock matches the given query.")

# View that manages and stores settings 
@login_required(login_url="login")
def transaction_settings_view(request, id):
    transaction = get_object_or_404(Transaction, id=id)

    # obtain price today
    today = datetime.date.today()
    stock_today = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
    while stock_today.count() == 0:
        today = get_prev_weekday(today)
        stock_today = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
    price_today = stock_today.values()[0]["c"]


    if transaction.user == request.user:
        # First retrieve the corresponding settings from the database
        if request.method == "GET":
            settings_form = TransactionSettingsForm(initial={"stock":transaction.stock,"portfolio":transaction.portfolio,"amount": transaction.amount, "label":transaction.label, "price_bought":transaction.price_bought, "buy_fees": transaction.buy_fees, "sell_fees": transaction.sell_fees, "buy_fees_constant": transaction.buy_fees_constant, "sell_fees_constant": transaction.sell_fees_constant, "buy_fees_linear": transaction.buy_fees_linear, "sell_fees_linear": transaction.sell_fees_linear, "lower_alert":transaction.lower_alert, "upper_alert":transaction.upper_alert, "date_bought": transaction.date_bought, "date_sold":transaction.date_sold})
        elif request.method == "POST":
            settings_form = TransactionSettingsForm(request.POST)
            if settings_form.is_valid():
                # If the form is valid get the relevant stock
                transaction = get_object_or_404(Transaction, id=id)
                # And update the settings
                transaction.stock = get_object_or_404(Stock, id=settings_form.data['stock'])
                transaction.amount = settings_form.data['amount']
                date = datetime.date(int(settings_form.data['date_bought_year']), int(settings_form.data['date_bought_month']), int(settings_form.data['date_bought_day']))
                if date.weekday() >= 5:
                    date = get_prev_weekday(date)

                transaction.date_bought = date
                transaction.label = settings_form.data["label"]
                transaction.price_bought = float(settings_form.data["price_bought"])

                # Calculate buy fees
                transaction.buy_fees_linear = settings_form.data["buy_fees_linear"]
                transaction.buy_fees_constant = settings_form.data["buy_fees_constant"]
                transaction.buy_fees = float(transaction.price_bought)*float(transaction.amount)*float(transaction.buy_fees_linear) + float(transaction.buy_fees_constant)

                # And the sell fees
                transaction_context = get_context(transaction)
                transaction.sell_fees_linear = settings_form.data["sell_fees_linear"]
                transaction.sell_fees_constant = settings_form.data["sell_fees_constant"]
                transaction.sell_fees = float(transaction.sell_fees_constant) + float(transaction.sell_fees_linear)*transaction_context["amount"]*transaction_context["current_price"]

                # Set alerts
                transaction.lower_alert = settings_form.data['lower_alert']
                transaction.upper_alert = settings_form.data['upper_alert']
                if transaction.lower_alert == "":
                    transaction.lower_alert = None
                if transaction.upper_alert == "":
                    transaction.upper_alert = None

                # Set the portfolio
                transaction.portfolio = settings_form.data["portfolio"]

                # Finally save them
                transaction.save()

                # Download the stock data for the last couple of days
                download_date = get_prev_weekday(datetime.date.today())
                # ToDo: we can get problems here in case the market was closed for 3 days maybe? or has that been taken care of somewhere?
                download_date = get_prev_weekday(download_date, days=3)
                download_stock_since(day=download_date.day, month=download_date.month, year=download_date.year, stock=transaction.stock)

                # And download user portfolio history since the date bought that has been entered
                download_user_portfolio_history_since.delay(username=request.user.username, date=date)

                return redirect("portfolio")
            else:
                # Throw an error?
                raise Http404("Transaction settings form not valid.")
        context = {"form": settings_form, "price_today": price_today}
        return render(request, "transaction_settings.html", context)
    else:
        raise Http404("No Stock matches the given query.")

# View to download stocks of a given transaction
# This view is currently required for the buttons in the transaction overview
@login_required(login_url="login")
def transaction_download_view(request, id, *args, **kwargs):
    transaction = get_object_or_404(Transaction, id=id)

    # obtain price today
    day = datetime.date.today()

    # Download the data
    download_stock_since(day=day.day, month=day.month, year=day.year, stock=transaction.stock)

    # And finally return to portfolio
    return redirect("portfolio")

@login_required(login_url="login")
def stock_creation_view(request, *args, **kwargs):
    if request.method == "GET":
        my_form = StockCreationForm()
    elif request.method == "POST":
        my_form = StockCreationForm(request.POST)
        if my_form.is_valid():
            stock = my_form.save(commit=False)

            # Save data and download stock data
            stock.save()
            return redirect("/transactions/create")
        else:
            # Throw an error?
            raise Http404("Stock creation form not valid.")
    context = {"form": my_form}
    return render(request, "stock_create.html", context)

@login_required(login_url="login")
def transaction_watch_view(request, *arg, **kwargs):
    # If we just get the page show the portfolio of the given user
    if request.method == "GET":
        watch_form = TransactionWatchForm()
        context = {"form": watch_form}
        return render(request, "transaction_watch.html", context)
    # Else show the form with the user we want to obtain
    elif request.method == "POST":
        # Obtain the form with the given entries
        watch_form = TransactionWatchForm(request.POST)
        if watch_form.is_valid():
            user = get_object_or_404(User, id=watch_form.data["user"])
            username = user.username

            # First obtain queryset for current portfolio ############################3
            portfolio = get_portfolio(username)
            merge_transactions(username)

            # List with dictionaries for final context to template
            queryset_portfolio = {}  # queryset = {"label1": [transaction1, transaction2, transaction3], "label2: [transaction1, transaction2, transaction3]"}

            for transaction in portfolio:
                ## Calculate and store relevant data
                transaction_context = get_context(transaction)

                # Set label to string for error handling
                if (transaction.label is None):
                    transaction.label = ""

                # Now we have to split the labels which are saved using / as seperator
                labels = transaction.label.split("/")
                # Loop through the labels
                for i in range(len(labels)):
                    label = labels[i]
                    # We only add the first label to the queryset for generation of the overview
                    if i == 0:
                        if label in queryset_portfolio:
                            queryset_portfolio[label].append(transaction_context)
                        else:
                            queryset_portfolio[label] = [transaction_context, ]

            # Create data for portfolio hisotry plotting
            user_portfolio_history = UserPortfolioHistory.objects.filter(user=request.user)
            user_portfolio_history = user_portfolio_history.order_by('date').reverse()

            # Create plotting data
            portfolio_plot_labels = []
            portfolio_plot_data = []
            portfolio_plot_profit = []
            for data in user_portfolio_history:
                portfolio_plot_labels.append(data.date.strftime("%Y-%m-%d"))
                portfolio_plot_data.append(data.price)
                portfolio_plot_profit.append(data.profit)

            # Obtain daily change
            index_error = False
            try:
                daily_change = round((portfolio_plot_data[0] - portfolio_plot_data[1]), 2)
                daily_change_perc = round((daily_change / portfolio_plot_data[0] * 100), 2)
            except (IndexError, ZeroDivisionError) as e:
                index_error = True

            # Find out whether all of the exchanges are still closed
            daily_from_today = True
            if index_error:
                daily_from_today = False
                try:
                    daily_change = round((portfolio_plot_data[0] - portfolio_plot_data[1]), 2)
                    daily_change_perc = round((daily_change / portfolio_plot_data[0] * 100), 2)
                except (IndexError, ZeroDivisionError):
                    daily_change_perc = 0


            try:
                initial_total_stocks = round(user_portfolio_history[0].invested, 2)
                current_total_profit = round(user_portfolio_history[0].profit, 2)
            except IndexError:
                print("Index error for user portfolio history")
                initial_total_stocks = 0
                current_total_profit = 0
            # And calculate the percentage
            if initial_total_stocks == 0:
                current_total_profit_perc = 0
            else:
                current_total_profit_perc = round(current_total_profit / initial_total_stocks * 100, 2)

            # Then obtain queryset for current history ############################3
            transactions = get_transactions(username)
            transactions = transactions.order_by(Coalesce('date_sold', 'date_bought')).reverse()
            queryset_history = {}
            today = datetime.date.today()
            for transaction in transactions:
                # Obtain current price
                stock_data = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
                i = 0
                while stock_data.count() == 0:
                    today = get_prev_weekday(today)
                    stock_data = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
                    i += 1
                    # This happens in case we add a historical stock for which no price is available. todo download data then and add to database
                    if i == 10:
                        break
                if stock_data.count() != 0:
                    price_today = stock_data.values()[0]["c"]
                else:
                    price_today = 0

                # Add links for both settings and plotting

                # Round all the relevant values and calculated profit
                transaction.price_bought = round(transaction.price_bought, 2)
                if transaction.buy_fees is not None:
                    transaction.buy_fees = round(transaction.buy_fees, 2)
                if transaction.sell_fees is not None:
                    transaction.sell_fees = round(transaction.sell_fees, 2)
                queryset_history[transaction.id] = {"transaction": transaction}
                if transaction.date_sold is not None:
                    transaction.price_sold = round(transaction.price_sold, 2)
                    # And add profit and total bank statement
                    queryset_history[transaction.id]["profit"] = round((
                                                                           transaction.price_sold - transaction.price_bought) * transaction.amount - transaction.buy_fees - transaction.sell_fees,
                                                               2)
                    queryset_history[transaction.id]["total"] = round(
                        transaction.price_sold * transaction.amount - transaction.sell_fees, 2)
                else:
                    # And add profit and total bank statement
                    queryset_history[transaction.id]["profit"] = round((
                                                                           price_today - transaction.price_bought) * transaction.amount - transaction.buy_fees - transaction.sell_fees,
                                                               2)
                    queryset_history[transaction.id]["total"] = round(price_today * transaction.amount - transaction.sell_fees,
                                                              1)
                # Last create links for plotting, settings and delete
                queryset_history[transaction.id]["plot_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)),
                                                                     "plot")
            # And finally render the page
            context = {"form": watch_form, "queryset_portfolio": queryset_portfolio, "current_total_profit_perc": current_total_profit_perc, "daily_change_perc": daily_change_perc, "daily_from_today": daily_from_today, "queryset_history": queryset_history}
            return render(request, "transaction_watch.html", context)

        else:
            # In case the watch form is not valid
            watch_form = TransactionWatchForm()
            context = {"form": watch_form}
            return render(request, "transaction_watch.html", context)

@login_required(login_url="login")
def transaction_history_view(request, *args, **kwargs):
    username = request.user.username
    transactions = get_transactions(username)
    transactions = transactions.order_by(Coalesce('date_sold', 'date_bought')).reverse()
    queryset = {}
    today = datetime.date.today()
    for transaction in transactions:
        # Obtain current price
        stock_data = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
        i = 0
        while stock_data.count() == 0:
            today = get_prev_weekday(today)
            stock_data = StockPriceHistory.objects.filter(ticker=transaction.stock, date=today)
            i += 1
            # This happens in case we add a historical stock for which no price is available. todo download data then and add to database
            if i == 10:
                break
        if stock_data.count() != 0:
            price_today = stock_data.values()[0]["c"]
        else:
            price_today = 0

        # Add links for both settings and plotting

        # Round all the relevant values and calculated profit
        transaction.price_bought = round(transaction.price_bought, 2)
        if transaction.buy_fees is not None:
            transaction.buy_fees = round(transaction.buy_fees, 2)
        if transaction.sell_fees is not None:
            transaction.sell_fees = round(transaction.sell_fees, 2)
        queryset[transaction.id] = {"transaction": transaction}
        if transaction.date_sold is not None:
            transaction.price_sold = round(transaction.price_sold, 2)
            # And add profit and total bank statement
            queryset[transaction.id]["profit"] = round((transaction.price_sold - transaction.price_bought) * transaction.amount - transaction.buy_fees - transaction.sell_fees, 2)
            queryset[transaction.id]["total"] = round(transaction.price_sold * transaction.amount - transaction.sell_fees, 2)
        else:
            # And add profit and total bank statement
            queryset[transaction.id]["profit"] = round((price_today - transaction.price_bought) * transaction.amount - transaction.buy_fees - transaction.sell_fees, 2)
            queryset[transaction.id]["total"] = round(price_today * transaction.amount - transaction.sell_fees, 1)
        # Last create links for plotting, settings and delete
        queryset[transaction.id]["plot_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "plot")
        queryset[transaction.id]["settings_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "settings_history")
        queryset[transaction.id]["delete_link"] = os.path.join(os.path.join("/transactions", str(transaction.id)), "delete")
    context = {"queryset": queryset}
    return render(request, "transaction_history.html", context)


@login_required(login_url="login")
def coming_soon_view(request, *args, **kwargs):
    context = {}
    return render(request, "coming_soon.html", context)

@login_required(login_url="login")
def transaction_rank_view(request, *args, **kwargs):
    # First find out what the user asked for plotting
    # If we just get the page set defaults settings and show the form
    if request.method == "GET":
        end_date = datetime.date.today()
        start_date = datetime.date(end_date.year, end_date.month, 1)
        date_range_form = DateRangeForm(initial={"start_date": start_date, "end_date": end_date})  # create form for rendering context
    # Else show the form with the user we want to obtain
    elif request.method == "POST":
        date_range_form = DateRangeForm(request.POST)
        start_date = datetime.date(int(date_range_form.data["start_date_year"]), int(date_range_form.data["start_date_month"]), int(date_range_form.data["start_date_day"]))
        end_date = datetime.date(int(date_range_form.data["end_date_year"]), int(date_range_form.data["end_date_month"]), int(date_range_form.data["end_date_day"]))

    # We have to decrease the start_date by one date as we normalize of the first day (otherwise the profits of the first day are not taken into account)
    # ToDo: Use Open and  close values
    start_date = start_date - datetime.timedelta(1)

    # First obtain all users and a start date which they have all in common
    users = User.objects.all().exclude(username="Test")
    start_date, allowed_users = obtain_start_date(users, start_date)

    # Generate a list of hexadecimal colors
    colours = list(mplt.colors.cnames.values())

    # Then create a dictionary which stores the plotting data per user
    user_data = {}
    
    # Create a pandas timeseries so that each day is contained 
    # This is required so that each plot has the same length
    date_range = pd.date_range(start_date, end_date)
    portfolio_plot_labels = list(date_range.strftime("%Y-%m-%d"))
    i = 0  # keep track of index to loop through colours afterwards
    for user in allowed_users:
        username = user.username
        
        # Obtain portfolio for the user
        portfolio = get_portfolio(username)

        # Create data for portfolio hisotry plotting
        user_portfolio_history = UserPortfolioHistory.objects.filter(user=user, date__range=[start_date, end_date])
        user_portfolio_history = user_portfolio_history.order_by('date').reverse()

        # Create plotting data for portfolio profit line chart
        portfolio_plot = pd.Series([np.nan]*len(date_range), index=date_range)
        # Obtain initial data invested at start data in order to normalize everything to the same starting position
        try:
            initial_invested = 0
            j = 0  # because the first date that the account is created all the data is set to 0, so we try to find the day after that
            while (initial_invested == 0 and j<user_portfolio_history.count()):
                initial_data = user_portfolio_history.reverse()[j]
                initial_invested = initial_data.invested
                initial_price = initial_data.price
                initial_profit = initial_data.profit
                j += 1
        except IndexError:
            initial_invested = 0
            initial_price = 0
            initial_profit = 0

        # Loop through the data and store it in the array
        for data in user_portfolio_history:
            if (data.invested) == 0:
                portfolio_plot[data.date] = 0
            else:
                current_difference = data.price - data.invested
                initial_difference = initial_price - initial_invested
                portfolio_plot[pd.to_datetime(data.date)] = (current_difference - initial_difference)/data.invested*100
        # Store the data in dictionaries for easier plotting
        portfolio_plot_data = {}
        portfolio_plot_data["labels"] = list(pd.to_datetime(portfolio_plot.index).strftime("%Y-%m-%m"))
        portfolio_plot_data["profit"] = list(portfolio_plot.values)
        # And take averages in case we did not have any value in the DB
        # None values
        for j in range(len(portfolio_plot_data["profit"])):
            # If we have a nan value then replace it with the value before that
            # ToDo take average over current and next value? 
            if portfolio_plot_data["profit"][j] != portfolio_plot_data["profit"][j]:
                if j == 0:
                    portfolio_plot_data["profit"][j] = 0
                else:
                    portfolio_plot_data["profit"][j] = portfolio_plot_data["profit"][j-1]

        # Take a random color from the list and increase the index
        portfolio_plot_data["colour"] = colours[i]
        if i < len(colours) - 2:
            i += 1
        else:
            i = 0
        
        # Add the data to the user
        user_data[username] = portfolio_plot_data

    context = {"date_range_form": date_range_form, "user_data": user_data, "portfolio_plot_labels": portfolio_plot_labels}
    return render(request, "transaction_rank.html", context)



@login_required(login_url="login")
def transaction_plot_view(request, id, *args, **kwargs):
    # Obtain stocks during that time period
    transaction = Transaction.objects.get(id=id)
    context = {"ticker": transaction.stock.plot_ticker}
    return render(request, "transaction_plot.html", context)
