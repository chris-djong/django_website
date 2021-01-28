import datetime
import os
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your vigws here.
@login_required(login_url="login")
def stock_analysis_view(request, *args, **kwargs):
    my_context = {}
    return render(request, "stock_analysis.html", my_context)
