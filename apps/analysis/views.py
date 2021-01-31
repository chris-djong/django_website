import datetime
import os
from .forms import StockForm
from .models import BalanceSheet, KeyStats, CashFlow, IncomeStatement
from ..stocks.models import Transaction, Stock
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your vigws here.
@login_required(login_url="login")
def stock_analysis_view(request, *args, **kwargs):
    # Obtain user object to filter stock
    required_stocks = Transaction.objects.filter(user=request.user, date_sold=None).values('stock').distinct()
    stocks = Stock.objects.filter(id__in=required_stocks)

    # Show stock form in the beginning
    stock_form = StockForm(stocks)
    
    if request.method == "GET":
        balance_sheet = None
        key_stats = None
        income_statement = None
        cash_flow = None
    elif request.method == 'POST':
        

        # Obtain alle the user stock which havve an entry for either key
        stock = get_object_or_404(Stock, id=stock_form.data['stock'])
        key_stats = KeyStats.objects.filter(stock=stock).order_by('-date')[0]
        balance_sheet = BalanceSheet.objects.filter(stock=stock).order_by('-date')[0]
        income_statement = IncomeStatement.filter(stock=stock).order_by('-date')[0]
        cash_flow = CashFlow.filter(stock=stock).order_by('-date')[0]

    my_context = {"form": stock_form, 'balance_sheet': balance_sheet, 'key_stats': key_stats, 'income_statement': income_statement, 'cash_flow': cash_flow}
    return render(request, "stock_analysis.html", my_context)
