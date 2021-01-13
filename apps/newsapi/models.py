from django.db import models
from ..stocks.models import Stock, Transaction
from django.contrib.auth.models import User

# Simple model to store the API key
class Newskey(models.Model):
    key = models.CharField(max_length=50)

# Model to store the articles themself
class Article(models.Model):
    # Remove the default here as well
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)  # the title of the article that is shown in the overview
    url = models.URLField(max_length=1000)  # the link to the article
    date = models.DateField() 
    text = models.CharField(max_length=20000)
    read = models.BooleanField(default=False)  # whether the article has been read by the user already
    sentiment = models.CharField(max_length=20)  # positive negative or neutral

    def __str__(self):
        return self.title
