from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('webhook/nelsius/', views.nelsius_webhook, name='nelsius_webhook'),
]
