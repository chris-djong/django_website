from django import forms
from .models import Transaction, Stock, CurrencyTicker
from django.contrib.auth.models import User
from django.forms.widgets import SelectDateWidget
import datetime


# Form to retrieve user
class UserForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())

# Form to retrieve date from user
class DateForm(forms.Form):
    date = forms.DateField(widget=SelectDateWidget(years=range(datetime.date.today().year, 2015, -1)))

# Form to retrieve date_range from user
class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=SelectDateWidget(years=range(datetime.date.today().year, 2015, -1)))
    end_date = forms.DateField(widget=SelectDateWidget(years=range(datetime.date.today().year, 2015, -1)))

# Form used for the creation of new transaction in the transaction overview
class TransactionCreationForm(forms.ModelForm):
    price_bought_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None)
    buy_fees_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None)
    sell_fees_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None)
    class Meta:
        model = Transaction
        fields = ['stock', 'amount', 'portfolio','label', 'date_bought', "price_bought", "buy_fees_linear", "buy_fees_constant", "sell_fees_linear", "sell_fees_constant"]
        widgets = {"date_bought": SelectDateWidget(years=range(datetime.date.today().year, 1985, -1))}

# Form used for the management of transactions in the transaction overview
class TransactionSettingsForm(forms.ModelForm):
    price_bought_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    price_sold_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    buy_fees_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    sell_fees_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    lower_alert_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    upper_alert_currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), empty_label=None, required=False)
    class Meta:
        model = Transaction
        fields = ['stock','amount','portfolio','label','date_bought',"price_bought",'buy_fees_linear','buy_fees_constant', "date_sold", "price_sold",'sell_fees_linear','sell_fees_constant','lower_alert','upper_alert']
        widgets = {'date_bought': SelectDateWidget(years=range(datetime.date.today().year, 1985, -1)), 'date_sold': SelectDateWidget(years=range(datetime.date.today().year, 1985, -1))}

# Form used for the creation of new stocks in the transaction overview
class StockCreationForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['ticker', 'article_ticker', 'iexfinance_ticker', 'plot_ticker', 'name', 'currency']


# Form used to change Stock settings / to change articles tickers etc for example /
class StockSettingsForm(forms.Form):
    ticker = forms.CharField(max_length=50, required=False)
    article_ticker = forms.CharField(max_length=50, required=False)
    plot_ticker = forms.CharField(max_length=50, required=False)
    name = forms.CharField(max_length=200, required=False)
    currency = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), required=False)

# Form used to pick a user to watch the portfolio from
class TransactionWatchForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['user']

