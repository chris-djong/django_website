import time
import os
from django.http import Http404, HttpResponseRedirect
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from ..stocks.functions import get_portfolio
from .models import Article
from .tasks import download_user_articles, download_all_user_articles
from ..stocks.forms import UserForm


# Create your views here.
@login_required(login_url="login")
def news_view(request, *args, **kwargs):
    # Identify user and pull his stocks
    username = request.user.username
    user = User.objects.get(username=username)

    # This time we only need the current portfolio as it is assumed that the transactions that have been sold are deleted already
    portfolio = get_portfolio(username)

    # Sort the articles in positive negative and neutral articles
    all_articles = {}

    # Next obtain the articles that are currently stored in the database and render them
    for transaction in portfolio:
        # Add the settings url
        settings_url = os.path.join(os.path.join("/stocks", str(transaction.stock.id)), "change_news_ticker")
        # In case we are currently downloading the articles then just simulate a fake articles dictionary
        # The template will change depending on whether this title is read
        all_articles[transaction.stock.article_ticker] = {}
        all_articles[transaction.stock.article_ticker]["Positive"] = Article.objects.filter(user=transaction.user, stock=transaction.stock, sentiment="Positive").order_by('-date')
        all_articles[transaction.stock.article_ticker]["Negative"] = Article.objects.filter(user=transaction.user, stock=transaction.stock, sentiment="Negative").order_by('-date')
        all_articles[transaction.stock.article_ticker]["Neutral"] = Article.objects.filter(user=transaction.user, stock=transaction.stock, sentiment="Neutral").order_by('-date')
        all_articles[transaction.stock.article_ticker]["settings_url"] = settings_url


    # Next we will sort all articles such that only the 5 latest are shown which have not been read yet 
    articles = {}
    for ticker, sentiments in all_articles.items():
        articles[ticker] = {}
        for sentiment, results in sentiments.items(): 
            n_articles_new = 0
            if sentiment == "settings_url":
                articles[ticker][sentiment] = results
            else:
                articles[ticker][sentiment] = {}
                articles[ticker][sentiment]["articles"] = []
                for article in results:
                    if type(article) != dict:
                        articles[ticker][sentiment]["articles"].append(article)
                        delete_url = os.path.join(os.path.join("/article", str(article.id)), "delete")
                        articles[ticker][sentiment]["articles"][-1].delete_url = delete_url
                        articles[ticker][sentiment]["articles"][-1].days_since = (article.date - datetime.date.today()).days
                        if not article.read:
                            n_articles_new += 1
        if sentiment == "settings_url":
            articles[ticker][sentiment]["n_articles_new"] = n_articles_new

                        
    # Render articles
    my_context = {"all_data": articles}
    return render(request, "news_view.html", my_context)


# Confirmation view for deletion of articles
@login_required(login_url="login")
def article_delete_view(request, id, *args, **kwargs):
    article = get_object_or_404(Article, id=id)
    if article.user == request.user:
        article.delete()
        return redirect("/news")
    else:
        raise Http404("No article matches the given query.")


# View that is rendered each time an article has been pressed / in order to keep track of which articles have been read 
@login_required(login_url="login")
def article_read_view(request, id, *args, **kwargs):
    # Verify whether user is allowed to modify the given transaction
    article = get_object_or_404(Article, id=id)
    if article.user == request.user:
        article.read = True
        article.save()
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        raise Http404("No article matches the given query.")
    
# Functions which downloads all the news articles for a given user
@login_required(login_url="login")
def article_download_view(request):
    if request.user.username == "chris":
        print("Downloading all user articles through API")
        download_all_user_articles.delay()
        return redirect("portfolio")
    else:
        raise Http404("Page not found")
