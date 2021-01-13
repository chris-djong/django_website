# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# General model that adds general information to the User that is useful to several modules
class UserInformation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_downloaded_stocks = models.DateTimeField(null=True)
    last_downloaded_articles = models.DateTimeField(null=True)

    def __str__(self):
        return self.user.username

