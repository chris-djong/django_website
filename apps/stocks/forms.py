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
    price_bought_to_eur = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), initial="Euro")
    buy_fees_to_eur = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), initial="Euro")
    sell_fees_to_eur = forms.ModelChoiceField(queryset=CurrencyTicker.objects.all(), initial="Euro")
    class Meta:
        model = Transaction
        fields = ['stock', 'amount', 'portfolio','label', 'date_bought', "price_bought", "buy_fees_linear", "buy_fees_constant", "sell_fees_linear", "sell_fees_constant"]
        widgets = {'date_bought': SelectDateWidget(years=range(datetime.date.today().year, 1985, -1))}

# Form used for the management of transactions in the transaction overview
class TransactionSettingsForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['stock','amount','portfolio','label','date_bought',"price_bought",'buy_fees_linear','buy_fees_constant', "date_sold", "price_sold",'sell_fees_linear','sell_fees_constant','lower_alert','upper_alert']
        widgets = {'date_bought': SelectDateWidget(years=range(datetime.date.today().year, 1985, -1)), 'date_sold': SelectDateWidget(years=range(datetime.date.today().year, 1985, -1))}

# Form used for the selling of a stock
class TransactionSellForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["date_sold", "price_sold"]
        widgets = {"date_sold": SelectDateWidget(years=range(datetime.date.today().year, 1985, -1))}

# Form used for the creation of new stocks in the transaction overview
class StockCreationForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['ticker', 'article_ticker', 'plot_ticker', 'name', 'currency']

# Form used to change Stock settings
# Also change in models.py if something changes here
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

