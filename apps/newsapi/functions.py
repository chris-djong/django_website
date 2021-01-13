
import requests
import datetime
from .models import Newskey, Article
from ..mail_relay.tasks import send_mail

# This function performs the actual api call and return the articles of that call
def perform_api_call(url, params):
    response = requests.get(url, params=params)
    # If we dont obtain a response from the server just do nothing and print the response to the log
    if not response:
        print("Error obtaining news:\n", response.json(), "\n\n")
        return None
    # Otherwise store the response in the database
    else:
        return response.json()["data"]

# Function that downloads all the articles that are newer than a given date 
def download_articles_since_date(transaction, since_date):
    # Whole process is similar to download_articles below 
    # In case of unclearance please see comments there
    key = Newskey.objects.all()[0].key

    # Then initialise the data for the API call
    url = "https://stocknewsapi.com/api/v1"
    ticker = transaction.stock.article_ticker
    article_mail_threshold = 3 
    total_n_articles = 0   # to keep track of average amount of articles per stock per day

    # Items are queried using the ticker and we want a maximum amount of 15 items. 
    # First we want 5 postive, then 5 negative and then 5 neutral articles
    # They are sorted using the interal ranking system of the stocknewsapi.com
    for sentiment in ["positive", "negative", "neutral"]:
        params = {"tickers": ticker, "items": 5, "token": key, "sortby": "rank", "sentiment": sentiment, "sourceexclude": "Zacks+Investment+Research,Seeking+Alpha"}  # for sources use a comma if you would like to include multiple sources / see stocknewsapi.com/documentation for a list ofr all news sources
        articles = perform_api_call(url, params)
        # Integer to keep track of total amount of articles for this sentiment
        n_articles = 0
        if articles is not None:
            for data in articles:
                # Convert str date to datetime object
                date_format = "%d %b %Y"
                date_split = data["date"].split(" ")
                date = date_split[1] + " " + date_split[2] + " " +  date_split[3]
                date = datetime.datetime.strptime(date, date_format)
                 
                # Only save the article if it is from today or from yesterday (as we download the articles in the morning we have to retrieve the ones that happened after the download as well)
                if since_date < datetime.datetime.date(date):
                    # And save it only in case it is not in the database already
                    if not Article.objects.filter(title=data["title"], url=data["news_url"], user=transaction.user).exists():
                        n_articles += 1
                        total_n_articles += 1
                        article = Article(stock=transaction.stock, user=transaction.user, title=data["title"], url=data["news_url"], date=date, text=data["text"], sentiment=data["sentiment"], read=False)
                        article.save()
            
        if n_articles > article_mail_threshold and sentiment != "neutral" and transaction.user.username == "chris": 
            subject = "%s sentiment - %s" % (sentiment, transaction.stock) 
            message = "Hello,\n\nMore than %d %s news articles have been detected for your '%s' transaction.\n\nFeel free to take a look at what is happening,\n\t https://finance.dejong.lu/news/\n\n" % (article_mail_threshold, sentiment, transaction.stock)
            send_mail("finance@dejong.lu", [transaction.user.email], subject, message)

    # Update average amount of articles per stock 
    transaction.stock.n_articles_avg = (transaction.stock.n_articles_avg * (31-1) + total_n_articles) / (31)
    transaction.stock.save()
    


# This function is called by a celery task in case the user has not downloaded the articles in a certain amount of time
# In the task, the function is called over every transaction that the user currently has in the portfolio
# It should perform the api call for the given article
# In order to perform multiple api calls for different sentiments, the actual calls are moved to the perform_api_call function 
def download_articles(transaction):
    # First obtain the key from the database
    key = Newskey.objects.all()[0].key

    # Then initialise the data for the API call
    url = "https://stocknewsapi.com/api/v1"
    ticker = transaction.stock.article_ticker
    article_mail_threshold = 3 
    total_n_articles = 0   # to keep track of average amount of articles per stock per day

    # Items are queried using the ticker and we want a maximum amount of 15 items. 
    # First we want 5 postive, then 5 negative and then 5 neutral articles
    # They are sorted using the interal ranking system of the stocknewsapi.com
    for sentiment in ["positive", "negative", "neutral"]:
        params = {"tickers": ticker, "items": 5, "token": key, "sortby": "rank", "sentiment": sentiment, "sourceexclude": "Zacks+Investment+Research,Seeking+Alpha"}  # for sources use a comma if you would like to include multiple sources / see stocknewsapi.com/documentation for a list ofr all news sources
        articles = perform_api_call(url, params)
        # Integer to keep track of total amount of articles for this sentiment
        n_articles = 0
        if articles is not None:
            for data in articles:
                today = datetime.datetime.today()

                # Convert str date to datetime object
                date_format = "%d %b %Y"
                date_split = data["date"].split(" ")
                date = date_split[1] + " " + date_split[2] + " " +  date_split[3]
                date = datetime.datetime.strptime(date, date_format)
                 
                # Only save the article if it is from today or from yesterday (as we download the articles in the morning we have to retrieve the ones that happened after the download as well)
                if (today - date).days < 2:
                    # And save it only in case it is not in the database already
                    if not Article.objects.filter(title=data["title"], url=data["news_url"], user=transaction.user).exists():
                        n_articles += 1
                        total_n_articles += 1
                        article = Article(stock=transaction.stock, user=transaction.user, title=data["title"], url=data["news_url"], date=date, text=data["text"], sentiment=data["sentiment"], read=False)
                        article.save()
            
        if n_articles > article_mail_threshold and sentiment != "neutral" and transaction.user.username == "chris": 
            subject = "%s sentiment - %s" % (sentiment, transaction.stock) 
            message = "Hello,\n\nMore than %d %s news articles have been detected for your '%s' transaction.\n\nFeel free to take a look at what is happening,\n\t https://finance.dejong.lu/news/\n\n" % (article_mail_threshold, sentiment, transaction.stock)
            send_mail("finance@dejong.lu", [transaction.user.email], subject, message)

    # Update average amount of articles per stock 
    transaction.stock.n_articles_avg = (transaction.stock.n_articles_avg * (31-1) + total_n_articles) / (31)
    transaction.stock.save()
