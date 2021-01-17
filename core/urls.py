# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from apps.stocks.views import transaction_overview_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main url goes to index
    path('', transaction_overview_view, name='home'),

    # User authentification pages
    path("", include("authentication.urls")),  # add this

    # Stock and transaction pages
    path("", include("apps.stocks.urls")),

    # Newsapi pages
    path("", include("apps.newsapi.urls")),

    # Predictor pages
    path("", include("apps.predictor.urls")),

    # Iexcloud pages
    path("", include("apps.iexcloud.urls")),
    ]
