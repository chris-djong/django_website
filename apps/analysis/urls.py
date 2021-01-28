from django.urls import path
from .views import stock_analysis_view

urlpatterns = [
    # Home
    path('analysis/', stock_analysis_view),
]

