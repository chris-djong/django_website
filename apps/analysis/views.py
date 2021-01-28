import datetime
import os
from .forms import StockForm
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your vigws here.
@login_required(login_url="login")
def stock_analysis_view(request, *args, **kwargs):
    # Show stock form in the beginning
    stock_form = StockForm()
    if request.method == "GET":
        print('Get form')
    elif request.method == 'POST':
        print('Post form')
    my_context = {"form": stock_form}
    return render(request, "stock_analysis.html", my_context)
