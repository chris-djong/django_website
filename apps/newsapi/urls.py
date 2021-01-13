
from django.urls import path
from .views import news_view, article_read_view, article_download_view, article_delete_view

urlpatterns = [
    path('news/', news_view, name='news'),
    path('article/<int:id>/read/', article_read_view, name="read_article"),
    path('article/<int:id>/delete/', article_delete_view, name="delete_article"),
    path('article/download/', article_download_view, name="download_article"),
]

