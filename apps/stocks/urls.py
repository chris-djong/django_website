from django.urls import path
from .views import transaction_overview_view, transaction_creation_view, transaction_delete_view, stock_download_since_view, transaction_settings_view, transaction_settings_history_view, stock_creation_view, coming_soon_view, transaction_watch_view, transaction_history_view, transaction_plot_view, transaction_rank_view, user_portfolio_download_view, stock_download_today_view, stock_change_article_ticker_view, transaction_download_view, transaction_settings_combined_view

urlpatterns = [
    # Home
    path('portfolio/', transaction_overview_view, name='portfolio'),
    path('watch/', transaction_watch_view, name="watch"),
    path('history/', transaction_history_view, name="history"),
    path('rank/', transaction_rank_view, name="rank"),

    # Modify transactions
    path('transactions/<str:portfolio>/create/', transaction_creation_view, name="create_transaction"),
    path('transactions/<int:id>/delete/', transaction_delete_view, name="delete_transaction"),
    path('transactions/<int:id>/settings/', transaction_settings_view, name="settings_transaction"),
    path('transactions/<int:id>/settings_history/', transaction_settings_history_view, name="settings_history_transaction"),
    path('transactions/<str:ids>/settings_combined/', transaction_settings_combined_view, name="settings_combined_transaction"),
    path('transactions/<int:id>/plot/', transaction_plot_view, name="plot_transaction"),

    # Modify stocks
    path('stocks/download/today/', stock_download_today_view, name="download_stocks_today"),
    path('stocks/download/since/', stock_download_since_view, name="download_stocks_since"),
    path('stocks/create/', stock_creation_view, name="create_stock"),
    path("stocks/<int:id>/change_news_ticker/", stock_change_article_ticker_view, name="news_view_change_stock"),

    # Download user portfolio
    path('users/portfolio/download/', user_portfolio_download_view, name="download_user_portfolio"),
]

