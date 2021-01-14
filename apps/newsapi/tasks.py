from .models import Article
from ..stocks.models import Transaction
from .functions import download_articles_since_date, download_articles
from core.celery import app
from django.contrib.auth.models import User
from ..mail_relay.tasks import send_mail
import datetime
from ..stocks.functions import get_portfolio, get_prev_weekday, get_next_weekday


# Function that downloads articles for a single transaction for a given date (used in create transaction for example)
@app.task
def download_articles_since(transaction_id, date):
    # First obtain the transaction
    transaction = Transaction.objects.get(id=transaction_id)

    # Just download the articles since one date before the given date to be sure
    # Transform date object from celery serialization to datetime
    date = datetime.date.fromisoformat(date.split("T")[0])
    date = get_prev_weekday(date)
    download_articles_since_date(transaction, date)

# This function uses the celery system to download the articles of a given user using api calls
# The articles are then stored in the database
@app.task
def download_user_articles(username):
    user = User.objects.get(username=username)
    
    # Dont download article data in case user has not logged in in the last 7 days
    last_login = user.last_login
    today = datetime.date.today()
    if (today - last_login).days < 7:

        # We need to query all the transactions here, because the ones which have been sold will be deleted in case there are any left
        transactions = get_portfolio(username)

        for transaction in transactions:
            # In case we did not sell the article then download the newest articles
            if transaction.date_sold is None:
                download_articles(transaction)  # obtain the articles


# Function that downloads the articles for each user
# This function will be executed by the celerybeat process daily
@app.task
def download_all_user_articles():
    users = User.objects.all()

    # Delete all the articles that are older than 7 days  
    current_articles = Article.objects.filter(date__lte=datetime.datetime.today() - datetime.timedelta(7))
    current_articles.delete()

    for user in users:
        download_user_articles(user.username)

