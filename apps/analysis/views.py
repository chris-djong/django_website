import datetime
import os
from .forms import StockForm
from .models import BalanceSheet, KeyStats
from ..stocks.models import Stock
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your vigws here.
@login_required(login_url="login")
def stock_analysis_view(request, *args, **kwargs):
    # Show stock form in the beginning
    stock_form = StockForm()
    if request.method == "GET":
        balance_sheet = None
    elif request.method == 'POST':
        stock = get_object_or_404(Stock, id=stock_form.data['stock'])
        key_stats = KeyStats.objects.filter(stock=stock).order_by('-date')[0]
        balance_sheet = BalanceSheet.objects.filter(stock=stock).order_by('-date')[0]

    my_context = {"form": stock_form, 'balance_sheet': balance_sheet, 'key_stats': key_stats}
    return render(request, "stock_analysis.html", my_context)
