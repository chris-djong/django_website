from django import forms
from ..stocks.models import Stock
import datetime

# Form to retrieve date from user
class StockForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=Stock.objects.none())

    def __init__(self, queryset):
        super(StockForm, self).__init__()
        self.fields['stock'].queryset = queryset


