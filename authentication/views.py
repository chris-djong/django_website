# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.shortcuts import render

from django.contrib.auth.decorators import login_required 
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.http import HttpResponse
from .forms import LoginForm, SignUpForm
from .models import UserInformation
from apps.mail_relay.tasks import send_mail

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:    
                msg = 'Invalid credentials'    
        else:
            msg = 'Error validating the form'    

    return render(request, "accounts/login.html", {"form": form, "msg" : msg})

def register_user(request):

    msg     = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            # Create UserInformation model for the new user 
            userobject = User.objects.get(username=username)
            user_information = UserInformation.objects.create(user=userobject)
            user_information.save()
            mail = form.data["email"]

            send_mail.delay("finance@dejong.lu", ["chris@dejong.lu"], "%s - Account Registration" % (user), "Empty")
            if mail is not None:
                send_mail.delay("finance@dejong.lu", [mail], "Account Registration", "Hello %s,\n\nYour account has been successfully generated.\n\nFeel free to test around.\n\nIn case you have any questions or features you would like to be implemented, please let us know under finance@dejong.lu\n\nKind regards,\nChris\n" % (username))

            msg     = 'User created.'
            success = True
            
        else:
            msg = 'Form is not valid'    
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg" : msg, "success" : success })


@login_required(login_url="login")
def user_settings_view(request):
    return render(request, "user_settings.html", {})

