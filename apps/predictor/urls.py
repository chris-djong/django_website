from django.urls import path
from .views import predictor_overview_view

urlpatterns = [
        path('indicators/', predictor_overview_view, name="predictore_overview"),
        ]
