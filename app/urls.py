from django.urls import path
from . import views


app_name = 'app'

urlpatterns = [
    path('api/transactions/', views.api_transactions, name='api_transactions'),
]
