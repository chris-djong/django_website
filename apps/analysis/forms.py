from django import forms
from ..stocks.models import Stock
import datetime

# Form to retrieve date from user
class StockForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=Stock.objects.all())


